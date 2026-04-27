from app import app, db
from app.models import GiftCard

with app.app_context():
    db.create_all()

    # Test card
    card = GiftCard(card_number="1234567890123456", pin="1234", balance=500.0)
    db.session.add(card)
    db.session.commit()