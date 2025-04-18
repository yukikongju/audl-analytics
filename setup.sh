
# activate virtual environment
python3 -m venv venv
source venv/bin/activate

# download python libraries
pip3 install -r requirements.txt

# create volumes
mkdir data/postgres

# install
brew install mongosh

# 
docker-compose up
