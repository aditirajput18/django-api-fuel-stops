## 🚗⛽ Route & Fuel Optimization API (Django)

This project is a Django-based API that returns an optimized driving route between two locations within the USA and calculates the most cost-effective fuel stops based on provided fuel price data.

The API determines:

🗺 Optimal driving route using a free routing API (OSRM)

⛽ Cheapest fuel stops within range

📍 Multiple stops if the vehicle cannot reach the destination on one tank

💵 Total estimated fuel cost

🖼 A static map preview of the route

📄 Optional UI view to visualize results

🔧 Tech Stack

Django 6

Django REST Framework

OSRM Public Routing API (free)

Fuel Data from local CSV file

EC2 Ubuntu deployment

✨ Features
✔ 1. Routing (Start → Finish)

The API calls OSRM Route API once:

https://router.project-osrm.org/route/v1/driving/LON,LAT;LON,LAT


This gives:

Total distance

Geo-coordinates along the path

Route polyline

Step-by-step path points

✔ 2. Fuel Stop Calculation

Assumptions given by assignment:

Vehicle range: 500 miles

Fuel efficiency: 10 MPG

Fuel data: Provided CSV file

The API:

Breaks the route into fuel-range segments

For each segment, finds nearby fuel stations (within radius)

Chooses the cheapest station

Saves it in the response

✔ 3. Cost Calculation
Gallons = total_miles / 10
Cost = gallons × fuel_price

✔ 4. Static Map Image

Generated using:

https://staticmap.openstreetmap.de/staticmap.php?...markers=...

📁 Project Structure
routeproject/
│── routeproject/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
│── routeapi/
│   ├── views.py
│   ├── urls.py
│   ├── utils.py
│   ├── templates/route.html  (optional UI)
│
│── data/
│   ├── fuel_prices.csv
│
└── manage.py

🚀 How to Run
1. Activate Virtual Env
source myenv/bin/activate

2. Run Server
python manage.py runserver 0.0.0.0:8000

🔥 API Endpoints
POST /api/route/

Compute route + fuel stops.

Example Request
{
  "start": "New York, NY",
  "finish": "Chicago, IL"
}

cURL
curl -X POST http://<EC2-IP>:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start":"New York, NY","finish":"Chicago, IL"}'

Example Response
{
  "distance_miles": 790.5,
  "estimated_total_gallons": 79.05,
  "estimated_total_cost_usd": 268.77,
  "fuel_stops": [
    {
      "id": "2",
      "name": "Exxon Station",
      "lat": 41.222,
      "lon": -74.222,
      "price": 3.40
    }
  ],
  "map_image_url": "https://staticmap.openstreetmap.de/..."
}

🎨 Optional Browser UI

Available at:

/route-ui/


Enter start and finish → See results nicely displayed.

☁ Deployment Notes (EC2)

Install Python + virtualenv

Clone repo

Add your IP to Django ALLOWED_HOSTS

Open EC2 port 8000

Start server with:

python manage.py runserver 0.0.0.0:8000

🔐 GitHub Deployment (PAT Token)

Create Classic Token → repo scope, then:

git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main

📌 OSRM API Usage

We use:

Free public routing engine
https://router.project-osrm.org

Endpoint:

/route/v1/driving/LON1,LAT1;LON2,LAT2?overview=full&geometries=geojson

📝 Summary

This assignment successfully demonstrates:

Django REST API development

Integration with a free routing API

Geo-coordinate operations

Fuel range and cost optimization

Static map rendering

Deployed on EC2

Working API via Apidog/Postman
