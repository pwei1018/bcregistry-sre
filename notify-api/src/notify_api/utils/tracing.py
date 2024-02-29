# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Centralized setup of tracing for the service."""
from functools import lru_cache, wraps

# https://cloud.google.com/trace/docs/setup/python-ot#import_and_configuration
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer


def init_trace(service_name: str, service_project: str, service_environment: str):
    """Init tracing."""
    LoggingInstrumentor().instrument(set_logging_format=True)

    set_global_textmap(CloudTraceFormatPropagator())

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.project": service_project,
            "service.environment": service_environment,
        }
    )

    # sampler = TraceIdRatioBased(1 / 50)

    tracer_provider = TracerProvider(resource=resource)
    cloud_trace_exporter = CloudTraceSpanExporter(resource_regex="service.*")
    tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))

    trace.set_tracer_provider(tracer_provider)


@lru_cache(maxsize=None)
def get_tracer() -> Tracer:
    """Generate tracer instance

    Usage:
        from trace import get_trace
        def do_something(self):
            tracer = get_trace()
            with tracer.start_as_current_span("Do something"):
                do_something
    """

    return trace.get_tracer(__name__)


def tracing(f):
    """Decorator method to add span to a method
    Reference: https://recruit.gmo.jp/engineer/jisedai/blog/gcp-cloud-trace/#anchor5

    Usage:
        from trace import tracing
        @tracing
        def do_something(self):
            do_something
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        tracer = get_tracer()
        with tracer.start_as_current_span(name=f.__qualname__):
            return f(*args, **kwargs)

    return wrapper


class TraceContextManager:
    """
    When an application running on Cloud Run or Cloud Functions receives a request, X-Cloud-Trace-Context is set in
    the HTTP request header, and the Trace ID and Span ID are entered here. Using this mechanism, when communicating
    between microservices, X-Cloud-Trace-Contextwe add the information we received to the header and issue a request to
    achieve distributed tracing.

    There seems to be a way to implement distributed tracing more easily by installing a package, etc., but I couldn't
    find the information & the number of codes to implement distributed tracing is small, so I can switch to another
    method.
    """

    @classmethod
    def __span_context(cls):
        return trace.get_current_span().get_span_context()

    @classmethod
    def get_trace_context(cls):
        """
        Distributed tracing requires passing the same trace context between applications.
        There may be an easier way to perform distributed tracing, but I have already implemented it using this method,
        which has been confirmed to work in a sample application.
        The format of X-Cloud-Trace-Context is TRACE_ID/SPAN_ID;o=TRACE_TRUE
        https://cloud.google.com/trace/docs/setup#force-trace
        """
        return f"{cls.get_trace_id()}/{cls.__get_span_id()}"

    @classmethod
    def get_trace_id(cls) -> str:
        """
        According to OpenTelemetry specifications, trace id is a 32-character hexadecimal value representing a 128-bit
        number.
        In Python's OpenTelemetry package, it is managed by int.
        It is necessary to use a formatting function on the package side.
        """
        return trace.format_trace_id(cls.__span_context().trace_id)

    @classmethod
    def __get_span_id(cls) -> int:
        return cls.__span_context().span_id
