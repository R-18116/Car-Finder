import os
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Use your API Key directly
GEMINI_API_KEY = "AIzaSyA1AWUTCYph39tyQzhdvdIs4jfDc3FCynQ"

def get_car_recommendations(car_type, budget, fuel_type, transmission, car_brand):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # Create the prompt including all parameters, handling empty values gracefully
    brand_text = f"{car_brand} " if car_brand else ""
    
    prompt = f"""
    Recommend 10 cars within a ₹{budget} budget for a {brand_text}{car_type} with:
    - Fuel Type: {fuel_type}
    - Transmission: {transmission}
    
    For each car, provide:
    - name (string): Full car name with year, make and model
    - price (string): Price formatted with dollar sign and commas
    - fuel_type (string): Type of fuel the car uses
    - transmission (string): Transmission type
    - features (object): With properties:
        - engine (string): Engine specifications
        - fuel_efficiency (string): MPG or efficiency rating
        - safety (string): Safety rating or features
    - description (string): A brief description of the car
    - image_url (string): Just use "placeholder" as we'll use a placeholder image
    
    Return ONLY valid JSON format like this (no other text or markdown):
    {{"recommendations": [
        {{
            "name": "Car Name",
            "price": "₹XX,XXX",
            "fuel_type": "Type",
            "transmission": "Type",
            "features": {{
                "engine": "Details",
                "fuel_efficiency": "XX MPG",
                "safety": "Rating"
            }},
            "description": "Brief description",
            "image_url": "placeholder"
        }}
    ]}}
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            response_json = response.json()
            
            try:
                model_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # Extract just the JSON part, handling both markdown code blocks and plain JSON
                if "```json" in model_response:
                    json_start = model_response.find("{")
                    json_end = model_response.rfind("}") + 1
                    json_data = model_response[json_start:json_end]
                else:
                    json_data = model_response.strip()
                
                # Parse the JSON data
                parsed_data = json.loads(json_data)
                
                # Make sure we have the expected structure
                if "recommendations" not in parsed_data or not isinstance(parsed_data["recommendations"], list):
                    return {"error": "Invalid response format from AI", "recommendations": []}
                
                return parsed_data
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                return {
                    "error": f"Failed to parse AI response: {str(e)}",
                    "recommendations": []
                }
        else:
            return {
                "error": f"API request failed with status code {response.status_code}",
                "recommendations": []
            }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Request error: {str(e)}",
            "recommendations": []
        }

@app.route('/get-car-recommendations', methods=['POST'])
def recommend_cars():
    try:
        data = request.get_json()
        
        # Extract and validate parameters
        car_type = data.get("carType", "")
        budget = data.get("budget", "50000")
        fuel_type = data.get("fuelType", "")
        transmission = data.get("transmission", "")
        car_brand = data.get("carBrand", "")
        
        # Add additional parameters from advanced filters if they exist
        advanced_params = {
            "seats": data.get("seats", ""),
            "year": data.get("year", ""),
            "condition": data.get("condition", ""),
            "drivetrain": data.get("drivetrain", ""),
            "features": data.get("features", [])
        }
        
        # Get recommendations
        recommendations = get_car_recommendations(car_type, budget, fuel_type, transmission, car_brand)
        
        return jsonify(recommendations)
    
    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}",
            "recommendations": []
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)