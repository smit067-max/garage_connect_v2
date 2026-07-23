import bcrypt
from bson import ObjectId
from datetime import datetime

# Users
def create_user(db, username, email, password, role, full_name, phone):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_doc = {
        "username": username,
        "email": email,
        "password": hashed,
        "role": role,
        "full_name": full_name,
        "phone": phone,
        "created_at": datetime.utcnow()
    }
    result = db.users.insert_one(user_doc)
    return result.inserted_id

def find_user_by_username(db, username):
    return db.users.find_one({"username": username})

def find_user_by_id(db, user_id):
    try:
        return db.users.find_one({"_id": ObjectId(user_id)})
    except:
        return None

def verify_password(stored_hash, password):
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# Garages
def create_garage(db, owner_id, name, address, city, phone, services, operating_hours):
    garage_doc = {
        "owner_id": ObjectId(owner_id),
        "name": name,
        "address": address,
        "city": city,
        "phone": phone,
        "services": services,
        "operating_hours": operating_hours,
        "is_approved": False,
        "rating": 0.0,
        "commission_rate": 0.15,
        "created_at": datetime.utcnow()
    }
    result = db.garages.insert_one(garage_doc)
    return result.inserted_id

def find_all_garages(db, approved_only=True, city=None, search=None):
    query = {}
    if approved_only:
        query["is_approved"] = True
    if city:
        query["city"] = {"$regex": f"^{city}$", "$options": "i"}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
        
    return list(db.garages.find(query).sort("rating", -1))

def find_garage_by_id(db, garage_id):
    try:
        return db.garages.find_one({"_id": ObjectId(garage_id)})
    except:
        return None

def find_garage_by_owner(db, owner_id):
    try:
        return db.garages.find_one({"owner_id": ObjectId(owner_id)})
    except:
        return None

def approve_garage(db, garage_id):
    db.garages.update_one({"_id": ObjectId(garage_id)}, {"$set": {"is_approved": True}})

def reject_garage(db, garage_id):
    db.garages.delete_one({"_id": ObjectId(garage_id)})

def update_garage_rating(db, garage_id):
    pipeline = [
        {"$match": {"garage_id": ObjectId(garage_id)}},
        {"$group": {"_id": "$garage_id", "avg_rating": {"$avg": "$rating"}}}
    ]
    result = list(db.reviews.aggregate(pipeline))
    if result:
        avg_rating = round(result[0]["avg_rating"], 1)
        db.garages.update_one({"_id": ObjectId(garage_id)}, {"$set": {"rating": avg_rating}})

# Bookings
def create_booking(db, customer_id, garage_id, service_type, vehicle_info, problem_description, ai_diagnosis, scheduled_date):
    booking_doc = {
        "customer_id": ObjectId(customer_id),
        "garage_id": ObjectId(garage_id),
        "service_type": service_type,
        "vehicle_info": vehicle_info,
        "problem_description": problem_description,
        "ai_diagnosis": ai_diagnosis,
        "scheduled_date": scheduled_date,
        "status": "Pending",
        "created_at": datetime.utcnow()
    }
    result = db.bookings.insert_one(booking_doc)
    return result.inserted_id

def find_bookings_by_customer(db, customer_id):
    return list(db.bookings.find({"customer_id": ObjectId(customer_id)}).sort("created_at", -1))

def find_bookings_by_garage(db, garage_id, status=None):
    query = {"garage_id": ObjectId(garage_id)}
    if status:
        query["status"] = status
    return list(db.bookings.find(query).sort("created_at", -1))

def update_booking_status(db, booking_id, new_status):
    db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": new_status}})

def complete_booking(db, booking_id, labour_price, parts_used):
    booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
    garage = find_garage_by_id(db, booking["garage_id"])
    
    parts_total = 0
    formatted_parts = []
    for part in parts_used:
        item = db.inventory.find_one({"_id": ObjectId(part["item_id"])})
        if item:
            cost = item["unit_price"] * part["quantity"]
            parts_total += cost
            update_stock(db, item["_id"], -part["quantity"])
            formatted_parts.append({
                "item_id": item["_id"],
                "name": item["name"],
                "quantity": part["quantity"],
                "unit_price": item["unit_price"],
                "total": cost
            })
            
    total_price = labour_price + parts_total
    commission_rate = garage.get("commission_rate", 0.15)
    commission_amount = total_price * commission_rate
    
    db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "status": "Completed",
            "labour_price": labour_price,
            "parts_used": formatted_parts,
            "parts_total": parts_total,
            "total_price": total_price,
            "commission_amount": commission_amount,
            "completed_at": datetime.utcnow()
        }}
    )

# Inventory
def add_inventory_item(db, garage_id, name, category, quantity, unit_price, low_stock_threshold):
    item_doc = {
        "garage_id": ObjectId(garage_id),
        "name": name,
        "category": category,
        "quantity": quantity,
        "unit_price": unit_price,
        "low_stock_threshold": low_stock_threshold,
        "created_at": datetime.utcnow()
    }
    result = db.inventory.insert_one(item_doc)
    return result.inserted_id

def get_inventory(db, garage_id, category=None):
    query = {"garage_id": ObjectId(garage_id)}
    if category:
        query["category"] = category
    return list(db.inventory.find(query).sort("name", 1))

def update_stock(db, item_id, quantity_change):
    db.inventory.update_one(
        {"_id": ObjectId(item_id)},
        {"$inc": {"quantity": quantity_change}}
    )

def get_low_stock_items(db, garage_id=None):
    query = {"$expr": {"$lte": ["$quantity", "$low_stock_threshold"]}}
    if garage_id:
        query["garage_id"] = ObjectId(garage_id)
    return list(db.inventory.find(query))

def delete_inventory_item(db, item_id):
    db.inventory.delete_one({"_id": ObjectId(item_id)})

# Reviews
def create_review(db, booking_id, customer_id, garage_id, rating, comment):
    review_doc = {
        "booking_id": ObjectId(booking_id),
        "customer_id": ObjectId(customer_id),
        "garage_id": ObjectId(garage_id),
        "rating": float(rating),
        "comment": comment,
        "created_at": datetime.utcnow()
    }
    db.reviews.insert_one(review_doc)
    update_garage_rating(db, garage_id)

def get_reviews_for_garage(db, garage_id):
    return list(db.reviews.find({"garage_id": ObjectId(garage_id)}).sort("created_at", -1))
