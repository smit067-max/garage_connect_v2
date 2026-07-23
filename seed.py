import random
from datetime import datetime, timedelta
import models

def seed_database(db):
    if db.users.count_documents({}) > 0:
        return

    random.seed(42)
    print("Seeding database...")

    # Users
    admin_id = models.create_user(db, "admin", "admin@garageconnect.com", "admin123", "admin", "System Admin", "9999999999")
    garage1_owner = models.create_user(db, "garage1", "ramesh@autoworks.com", "garage123", "garage_owner", "Ramesh Kumar", "9876543210")
    garage2_owner = models.create_user(db, "garage2", "speedy@motors.com", "garage123", "garage_owner", "Speedy Singh", "9876543211")
    cust1_id = models.create_user(db, "customer1", "cust1@mail.com", "cust123", "customer", "Rahul Sharma", "9876543212")
    cust2_id = models.create_user(db, "customer2", "cust2@mail.com", "cust123", "customer", "Priya Verma", "9876543213")

    # Garages
    services = ["Oil Change", "Brake Repair", "Engine Repair", "AC Repair"]
    garage1_id = models.create_garage(db, garage1_owner, "Ramesh Auto Works", "Sector 45", "Gurugram", "9876543210", services, "9 AM - 6 PM")
    models.approve_garage(db, garage1_id)
    db.garages.update_one({"_id": garage1_id}, {"$set": {"commission_rate": 0.15}})

    garage2_id = models.create_garage(db, garage2_owner, "Speedy Motors", "MG Road", "Bangalore", "9876543211", services + ["Body Repair"], "10 AM - 8 PM")
    models.approve_garage(db, garage2_id)
    db.garages.update_one({"_id": garage2_id}, {"$set": {"commission_rate": 0.12}})

    # Inventory
    categories = ["Brakes", "Engine", "Electrical", "Filters", "Fluids", "Body"]
    g1_inventory = []
    g2_inventory = []
    for i in range(10):
        g1_inventory.append(models.add_inventory_item(db, garage1_id, f"Part G1-{i}", random.choice(categories), random.randint(5, 50), random.randint(200, 3000), 5))
        g2_inventory.append(models.add_inventory_item(db, garage2_id, f"Part G2-{i}", random.choice(categories), random.randint(5, 50), random.randint(200, 3000), 5))

    # Bookings & Reviews
    now = datetime.utcnow()
    customers = [cust1_id, cust2_id]
    garages = [(garage1_id, g1_inventory, 0.15), (garage2_id, g2_inventory, 0.12)]
    
    for i in range(50):
        cust = random.choice(customers)
        g_id, g_inv, comm_rate = random.choice(garages)
        service = random.choice(services)
        
        # Random past date
        days_ago = random.randint(1, 180)
        created_at = now - timedelta(days=days_ago)
        
        booking_id = models.create_booking(db, cust, g_id, service, "Maruti Swift", "Car has issues", {}, created_at.strftime("%Y-%m-%d"))
        
        # Manually backdate created_at
        db.bookings.update_one({"_id": booking_id}, {"$set": {"created_at": created_at}})
        
        status = random.choices(["Pending", "Accepted", "In Progress", "Completed"], weights=[5, 10, 10, 75])[0]
        
        if status != "Pending":
            models.update_booking_status(db, booking_id, status)
            
        if status == "Completed":
            parts_used = []
            num_parts = random.randint(0, 3)
            selected_parts = random.sample(g_inv, num_parts)
            for part_id in selected_parts:
                parts_used.append({"item_id": part_id, "quantity": random.randint(1, 2)})
                
            labour_price = random.randint(500, 5000)
            models.complete_booking(db, booking_id, labour_price, parts_used)
            
            # Backdate completed_at
            completed_at = created_at + timedelta(days=random.randint(1, 3))
            db.bookings.update_one({"_id": booking_id}, {"$set": {"completed_at": completed_at}})
            
            # 20% chance of review
            if random.random() < 0.2:
                rating = random.randint(3, 5)
                models.create_review(db, booking_id, cust, g_id, rating, "Good service")

    print("Database seeding completed.")
