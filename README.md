# Smart Travel Planner (B.Tech First Year Mini Project)

A tour & travels web app. The user enters budget, days, travellers and trip type; the Flask backend suggests destinations that fit the budget with a day-wise itinerary, and lets the user book / cancel trips.

## Mapping to Class Test-2 lab evaluation
| Task | Where it is done |
|---|---|
| a. Backend using Python | `app.py` (logic: cost estimation, budget filter, SQLite database) |
| b. Flask app with routes and HTTP methods; deploy API | `app.py` routes (GET, POST, PUT, DELETE) + deployment steps below |
| c. Integrate backend with frontend using API | `templates/index.html` uses `fetch()` to call the API |
| d. Discussion and evaluation | Viva questions at the end |

## Folder structure
```
smart-travel-planner/
├── app.py
├── requirements.txt
├── Procfile
├── README.md
└── templates/
    └── index.html
```

## Run locally
```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## API endpoints
| Method | URL | Purpose |
|---|---|---|
| GET | /api/destinations?type=beach | List destinations (optional filter) |
| GET | /api/destinations/<id> | One destination (404 if missing) |
| POST | /api/plan | Suggest trips for budget/days/travellers/type |
| POST | /api/bookings | Create booking (201) |
| GET | /api/bookings | List bookings |
| PUT | /api/bookings/<id> | Update travellers/days |
| DELETE | /api/bookings/<id> | Cancel booking |

Test with curl:
```
curl -X POST http://127.0.0.1:5000/api/plan -H "Content-Type: application/json" -d "{\"budget\":30000,\"days\":4,\"travellers\":2}"
```
(You can also test in Postman for the lab demo.)

## Deploy (free) on Render
1. Push this folder to a GitHub repo.
2. render.com -> New -> Web Service -> connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy. You get a public URL; the same URL serves both the website and the API.
(Alternative: PythonAnywhere free account -> upload files -> create a Flask web app.)
Note: free hosting may reset the SQLite file on restart; fine for a demo.

## Viva questions (discussion and evaluation)
1. What is an API / REST? -> A way for frontend and backend to talk over HTTP using URLs and methods, returning JSON.
2. Difference between GET, POST, PUT, DELETE? -> read, create, update, remove.
3. What does `jsonify` do? -> Converts Python dict/list to a JSON response.
4. What are status codes 200, 201, 400, 404? -> OK, Created, bad input, not found.
5. Why SQLite? -> Lightweight, built into Python, no server needed.
6. How is the cost estimated? -> stay (cost/day x days x people) + return transport x people.
7. How does the frontend connect? -> `fetch()` sends requests to `/api/...` and updates the page with the JSON.
8. What is `gunicorn`? -> Production server used instead of Flask's development server.
9. Future scope: real hotel/flight APIs, login, maps, weather, payments.
