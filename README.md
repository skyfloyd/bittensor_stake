# Take-Home Coding Task – Senior Python Backend Engineer

## Setup

Current application requires Python 3.10.

Rename `.env.example` file to `.env` and set all necessary variable values.

### Run on docker

>docker-compose up --build

You can check mongodb results by
>docker exec -it bittensor_stake-mongodb-1 mongosh bittensor_stake --eval "db.stake.find().pretty()"

Where `bittensor_stake-mongodb-1` is MongoDB container name and `bittensor_stake` is the database name.

### Run on local

Create virtual environment
> python3 -m venv venv

Activate virtual environment
> source venv/bin/activate
 
Install dependencies from requirements.txt
> pip install -r requirements.txt

Make sure that MongoDB and Redis services are on

Start the FastAPI server
>uvicorn app.main:app --reload --port 8000

In a separate terminal, start the Celery worker
>celery -A app.core.celery_app worker --loglevel=info

Just make sure that your requests header contains 
`Authorization: Bearer api-very-secret-token`

You can modify `api-very-secret-token` by changing `API_TOKEN` environment variable.

Get request example

```
curl --location 'http://127.0.0.1:8000/api/v1/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v&trade=true' \
--header 'Authorization: Bearer api-very-secret-token'
```


## Tasks status
1. Docker `[Done]`
2. FastAPI with Authorization `[Done]`
3. Cache with Redis `[Done]`
4. Dividends query `[Done]`
5. Twitter search `[Done]`
6. Get a sentiment `[Done]`
7. Add/Remove stake (branch: stake_service_test) `[Not working yet]`
8. Background Celery task `[Done]`
9. Save results in DB `[Done]`
10. Pytest `[Not implemented]`


Main sources are in the `develop` branch. As I didn't have time to clean up everything for production I did not move them to `main` or `master` branch.

Add/Remove stake functionality is located at `stake_service_test`. As it is not working properly I did not move them to `develop` branch.