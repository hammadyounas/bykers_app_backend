from flask import Flask, request, jsonify
import pymongo
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB Configuration
# app.config["MONGO_URI"] = "mongodb://localhost:27017/bike_marketplace"
# mongo = pymongo(app)
client = pymongo.MongoClient("mongodb+srv://hammadyounas:hammadyounas@testcluster.bi2khpc.mongodb.net/")
db = client["bike_marketplace"]
sellers = db["sellers"]
buyers = db["buyers"]
bikes = db["bikes"]


# Seller Route: Submit Bike Information
@app.route('/sell/bike', methods=['POST'])
def sell_bike():
    data = request.json
    bike_id = bikes.insert_one({
        "title": data['title'],
        "model": data['model'],
        "engine": data['engine'],
        "registered_in": data['registered_in'],
        "purchased_year": data['purchased_year'],
        "petrol_capacity_per_litre": data['petrol_capacity_per_litre'],
        "total_mileage": data['total_mileage'],
        "location": data['location'],
        "selling_price": data['selling_price'],
        "description": data['description'],
        "images": data['images'],
        "contact": {
            "name": data['name'],
            "mobile_info": data['mobile_info'],
            "email": data['email']
        },
        "approved": False
    })
    return jsonify({"message": "Bike submitted successfully!", "bike_id": str(bike_id.inserted_id)})

# Buyer Route: View All Bikes
@app.route('/bikes', methods=['GET'])
def get_bikes():
    all_bikes = bikes.find({"approved": True})
    bike_list = []
    for bike in all_bikes:
        bike['_id'] = str(bike['_id'])
        bike_list.append(bike)
    return jsonify(bike_list)

# Buyer Route: View Bike Details
@app.route('/bike/<bike_id>', methods=['GET'])
def get_bike(bike_id):
    bike = bikes.find_one({"_id": ObjectId(bike_id), "approved": True})
    if bike:
        bike['_id'] = str(bike['_id'])
        return jsonify(bike)
    else:
        return jsonify({"error": "Bike not found"}), 404

# Buyer Route: Express Interest in Bike
@app.route('/buy', methods=['POST'])
def buy_bike():
    data = request.json
    buyer_id = buyers.insert_one({
        "name": data['name'],
        "email": data['email'],
        "phone_number": data['phone_number'],
        "description": data['description'],
        "interested_in_test_ride": data['interested_in_test_ride'],
        "bike_id": ObjectId(data['bike_id']),
        "status": "pending for contact"
    })
    return jsonify({"message": "Interest submitted successfully!", "buyer_id": str(buyer_id.inserted_id)})

# Admin Route: Approve Bike Listing
@app.route('/admin/approve/<bike_id>', methods=['PATCH'])
def approve_bike(bike_id):
    result = bikes.update_one({"_id": ObjectId(bike_id)}, {"$set": {"approved": True}})
    if result.modified_count:
        return jsonify({"message": "Bike approved successfully!"})
    else:
        return jsonify({"error": "Bike not found or already approved"}), 404

# Admin Route: View All Inquiries
@app.route('/admin/inquiries', methods=['GET'])
def get_inquiries():
    all_inquiries = buyers.find()
    inquiry_list = []
    for inquiry in all_inquiries:
        inquiry['_id'] = str(inquiry['_id'])
        inquiry['bike_id'] = str(inquiry['bike_id'])
        inquiry_list.append(inquiry)
    return jsonify(inquiry_list)

# Admin Route: Update Inquiry Status
@app.route('/admin/inquiry/<inquiry_id>', methods=['PATCH'])
def update_inquiry_status(inquiry_id):
    data = request.json
    result = buyers.update_one({"_id": ObjectId(inquiry_id)}, {"$set": {"status": data['status']}})
    if result.modified_count:
        return jsonify({"message": "Inquiry status updated successfully!"})
    else:
        return jsonify({"error": "Inquiry not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
