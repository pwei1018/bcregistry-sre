
#!/bin/bash

#declare -a users=("bcregistry-sre@gov.bc.ca")
#declare -a users=("vysakh.menon@gov.bc.ca" "severin.beauvais@gov.bc.ca" "karim.jazzar@gov.bc.ca" "argus@daxiom.com")
#declare -a users=("jia.xu@gov.bc.ca" "chiu.oddyseus@gov.bc.ca" "travis.semple@gov.bc.ca")
declare -a users=("jazzar.karim@gmail.com")
#declare -a users=("doug@daxiom.com")
#declare -a users=("omid.x.zamani@gov.bc.ca" "meng.dong@gov.bc.ca" "eve.deng@gov.bc.ca" "richard.armitage@gov.bc.ca" "steven.chen@gov.bc.ca")
#declare -a users=("david.roberts@gov.bc.ca" "genevieve.primeau@gov.bc.ca" "siddharth.chaturvedi@gov.bc.ca")

#declare -a all_projects=("a083gt" "mvnjri" "gtksf3" "yfjq17" "c4hnrd" "k973yf" "yfthig" "eogruh")
#declare -a projects=("gtksf3" "c4hnrd" "yfthig") ##relationship
declare -a projects=("a083gt" "c4hnrd" "yfthig") ##business
#declare -a projects=("eogruh" "c4hnrd" "yfthig") ##assets
#declare -a projects=("yfjq17" "c4hnrd" "yfthig") ##btr
#declare -a projects=("c4hnrd" "yfthig") ##names
#declare -a projects=("mvnjri" "c4hnrd" "yfthig") ##analytics
#declare -a projects=("c4hnrd")

declare -a environments=("dev" "test" "tools")
#declare -a environments=("dev" "test" "tools" "prod" "integration" "sandbox")
declare -a roles=("developer")

for user in "${users[@]}"
do
    echo "user: $user"
    for ev in "${environments[@]}"
    do
        for ns in "${projects[@]}"
        do
            echo "project: $ns-$ev"
            PROJECT_ID=$ns-$ev

            if [[ ! -z `gcloud projects describe ${PROJECT_ID} --verbosity=none` ]]; then
                gcloud config set project ${PROJECT_ID}

                for ro in "${roles[@]}"
                do
                    ROLE_NAME="projects/${PROJECT_ID}/roles/role$ro"
                    echo "role: $ROLE_NAME"

                    gcloud projects add-iam-policy-binding $PROJECT_ID --member user:$user --role=$ROLE_NAME --condition=None --verbosity=none --quiet
                done
            fi
        done
    done
done