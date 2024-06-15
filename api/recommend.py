from flask import Flask, request, jsonify
import pandas as pd
import requests
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

# Replace 'YOUR_API_KEY' with your actual API key weather
api_key = '867d9c2c06bc4e7fa29124152241406'

# Load the places data from CSV into a pandas DataFrame
try:
    places_data = pd.read_csv('places_data.csv')
except FileNotFoundError:
    print("Error: places_data.csv file not found. Please ensure the file exists and the path is correct.")
    exit(1)

def get_weather_forecast(api_key, city, start_date, num_days):
    base_url = 'http://api.weatherapi.com/v1/forecast.json'
    forecasts = []
    
    try:
        for i in range(num_days):
            date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
            url = f'{base_url}?key={api_key}&q={city}&dt={date}&days=1'
            response = requests.get(url)
            data = response.json()
            
            # Example of extracting some information
            location = data['location']['name']
            forecast_day = data['forecast']['forecastday'][0]
            date = forecast_day['date']
            max_temp_c = forecast_day['day']['maxtemp_c']
            min_temp_c = forecast_day['day']['mintemp_c']
            condition = forecast_day['day']['condition']['text']
            
            # Store the forecast information
            forecast_info = {
                'date': date,
                'location': location,
                'max_temp_c': max_temp_c,
                'min_temp_c': min_temp_c,
                'condition': condition
            }
            forecasts.append(forecast_info)
        
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    return forecasts

@app.route('/api/recommend', methods=['POST','GET'])
def recommend():
    try:
        data = request.get_json(force=False,silent=False,cache=True)
        print("Received data:", data)

        # Retrieve user preferences from the request
        preferences = data.get('preferences', {})

        # Calculate recommendation scores for each place based on user preferences
        scores = []
        for index, row in places_data.iterrows():
            score = 0
            for field in preferences:
                if row[field] == preferences[field]:
                    score += 1
            scores.append(score)

        # Add scores to places_data as a new column
        places_data['score'] = scores

        # Sort places by score in descending order and select top 5
        recommended_places = places_data.sort_values(by='score', ascending=False).head(5)['Place'].tolist()

        # Get start_date and end_date from the request
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Calculate num_days dynamically
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        num_days = (end_date_obj - start_date_obj).days + 1

        # Fetch weather forecasts for recommended places
        forecast_report = []
        for place in recommended_places:
            forecasts = get_weather_forecast(api_key, place, start_date, num_days)
            forecast_report.append({place: forecasts})

        return jsonify({
            'recommended_places': recommended_places,
            'forecast_report': forecast_report
        }), 200

    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        return jsonify({'error': error_message}), 500


if __name__ == '__main__':
    app.run(debug=True)
