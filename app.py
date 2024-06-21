from flask import Flask, request, jsonify, send_file
import pymongo
from gridfs import GridFS
from bson.objectid import ObjectId
from io import BytesIO

app = Flask(__name__)

# MongoDB Configuration
# app.config["MONGO_URI"] = "mongodb://localhost:27017/bike_marketplace"
# mongo = pymongo(app)
client = pymongo.MongoClient("mongodb://localhost:27017/bike_marketplace")
db = client["bike_marketplace"]
sellers = db["sellers"]
buyers = db["buyers"]
bikes = db["bikes"]
fs = GridFS(db)

# Seller Route: Submit Bike Information
@app.route('/sell/bike', methods=['POST'])
def sell_bike():
    # Parse non-file form data
    title = request.form['title']
    model = request.form['model']
    engine = request.form['engine']
    registered_in = request.form['registered_in']
    purchased_year = request.form['purchased_year']
    petrol_capacity_per_litre = request.form['petrol_capacity_per_litre']
    total_mileage = request.form['total_mileage']
    location = request.form['location']
    selling_price = request.form['selling_price']
    description = request.form['description']
    name = request.form['name']
    mobile_info = request.form['mobile_info']
    email = request.form['email']
    bike_condition = request.form['condition']  # New field to indicate if the bike is new or used

    # Handle image uploads
    image_ids = []
    if 'images' in request.files:
        for image in request.files.getlist('images'):
            image_id = fs.put(image, content_type=image.content_type, filename=image.filename)
            image_ids.append(image_id)

    bike_id = db.bikes.insert_one({
        "title": title,
        "model": model,
        "engine": engine,
        "registered_in": registered_in,
        "purchased_year": purchased_year,
        "petrol_capacity_per_litre": petrol_capacity_per_litre,
        "total_mileage": total_mileage,
        "location": location,
        "selling_price": selling_price,
        "description": description,
        "images": image_ids,
        "contact": {
            "name": name,
            "mobile_info": mobile_info,
            "email": email
        },
        "approved": False,
        "condition": bike_condition  # Store the condition of the bike
    })

    return jsonify({"message": "Bike submitted successfully!", "bike_id": str(bike_id.inserted_id)})

# Buyer Route: View All Bikes with Pagination
@app.route('/bikes', methods=['GET'])
def get_bikes():
    # Pagination parameters
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    skip = (page - 1) * limit

    all_bikes = db.bikes.find({"approved": True}).skip(skip).limit(limit)
    total_bikes = db.bikes.count_documents({"approved": True})
    total_pages = (total_bikes + limit - 1) // limit  # Calculate total pages

    bike_list = []
    for bike in all_bikes:
        bike['_id'] = str(bike['_id'])
        bike['images'] = [str(image_id) for image_id in bike.get('images', [])]
        bike_list.append(bike)

    return jsonify({
        "total_bikes": total_bikes,
        "total_pages": total_pages,
        "current_page": page,
        "bikes": bike_list
    })

# Buyer Route: View Unapproved Bikes (new endpoint)
@app.route('/bikes/list', methods=['GET'])
def get_unapproved_bikes():
    # Pagination parameters
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    skip = (page - 1) * limit

    all_bikes = db.bikes.find().skip(skip).limit(limit)
    total_bikes = db.bikes.count_documents({"approved": True})
    total_pages = (total_bikes + limit - 1) // limit  # Calculate total pages

    bike_list = []
    for bike in all_bikes:
        bike['_id'] = str(bike['_id'])
        bike['images'] = [str(image_id) for image_id in bike.get('images', [])]
        bike_list.append(bike)

    return jsonify({
        "total_bikes": total_bikes,
        "total_pages": total_pages,
        "current_page": page,
        "bikes": bike_list
    })

# Buyer Route: View Bike Details
@app.route('/bike/<bike_id>', methods=['GET'])
def get_bike(bike_id):
    bike = db.bikes.find_one({"_id": ObjectId(bike_id), "approved": True})
    if bike:
        bike['_id'] = str(bike['_id'])
        bike['images'] = [str(image_id) for image_id in bike.get('images', [])]
        return jsonify(bike)
    else:
        return jsonify({"error": "Bike not found"}), 404

# Buyer Route: Express Interest in Bike
@app.route('/buy', methods=['POST'])
def buy_bike():
    data = request.json
    buyer_id = db.buyers.insert_one({
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
    result = db.bikes.update_one({"_id": ObjectId(bike_id)}, {"$set": {"approved": True}})
    if result.modified_count:
        return jsonify({"message": "Bike approved successfully!"})
    else:
        return jsonify({"error": "Bike not found or already approved"}), 404

# Admin Route: View All Inquiries
@app.route('/admin/inquiries', methods=['GET'])
def get_inquiries():
    all_inquiries = db.buyers.find()
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
    result = db.buyers.update_one({"_id": ObjectId(inquiry_id)}, {"$set": {"status": data['status']}})
    if result.modified_count:
        return jsonify({"message": "Inquiry status updated successfully!"})
    else:
        return jsonify({"error": "Inquiry not found"}), 404

# New Route: Access Image by ID
@app.route('/image/<image_id>', methods=['GET'])
def get_image(image_id):
    try:
        print('check')
        image = fs.get(ObjectId(image_id))
        return send_file(BytesIO(image.read()), mimetype=image.content_type, as_attachment=False, download_name=image.filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True)
