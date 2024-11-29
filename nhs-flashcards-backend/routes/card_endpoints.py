from flask import request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from uuid import UUID

from database.db_interface import db
from database.db_types import Card, Group, User

# Create Card Endpoint
@jwt_required()
def create_card():
    data = request.get_json()
    question = data.get('question')
    correct_answer = data.get('correct_answer')
    incorrect_answer = data.get('incorrect_answer')
    group_id = UUID(data.get('group_id'))

    if not all([question, correct_answer, group_id]):
        return jsonify({'message': 'Missing required fields'}), 400

    user_id = get_jwt_identity()
    user_uuid = UUID(user_id)
    user = User.query.filter_by(id=user_uuid).first()
    user_groups = user.subscribed_groups.all()

    # Check if the user is subscribed to the group
    if group_id not in [group.group_id for group in user_groups]:
        return jsonify({'message': 'User is not subscribed to the group'}), 403

    # Check if the group exists
    if not Group.query.filter_by(group_id=group_id).first():
        return jsonify({'message': 'Group not found'}), 404

    # Create new card
    new_card = Card(
        question=question,
        correct_answer=correct_answer,
        incorrect_answer=incorrect_answer,
        group_id=group_id,
        creator_id=user_uuid,
        updated_by_id=user_uuid
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'card_id': new_card.card_id}), 201

# Get Card Endpoint
@jwt_required()
def get_card(card_id):
    """Only return cards that a user has subscribed to the corresponding group"""
    card_id = request.view_args['card_id']
    user_id = get_jwt_identity()
    user_uuid = UUID(user_id)

    card = Card.query.filter_by(card_id=card_id).first()
    if not card:
        return jsonify({'message': 'Card not found'}), 404

    # Check that the user is subscribed to the group of the card
    user = User.query.filter_by(id=user_uuid).first()
    user_groups =  user.subscribed_groups.all()
    if card.group_id not in [group.group_id for group in user_groups]:
        return jsonify({'message': 'User is not subscribed to the group'}), 403

    card_data = {
        'card_id': card.card_id,
        'question': card.question,
        'correct_answer': card.correct_answer,
        'incorrect_answer': card.incorrect_answer,
        'group_id': card.group_id,
        'creator_id': card.creator_id,
        'time_created': card.time_created,
        'time_updated': card.time_updated,
        'updated_by_id': card.updated_by_id
    }

    return jsonify(card_data), 200

# Get Cards Endpoint
@jwt_required()
def get_cards():
    """Only return cards that a user has subscribed to the corresponding group"""
    user_id = get_jwt_identity()
    user_uuid = UUID(user_id)

    # Get all groups that the user has subscribed to
    user = User.query.filter_by(id=user_uuid).first()
    user_groups =  user.subscribed_groups.all()
    # And get the cards that belong to those groups
    cards = Card.query.filter(Card.group_id.in_([group.group_id for group in user_groups])).all()

    cards_list = [{
        'card_id': card.card_id,
        'question': card.question,
        'correct_answer': card.correct_answer,
        'incorrect_answer': card.incorrect_answer,
        'group_id': card.group_id,
        'creator_id': card.creator_id,
        'time_created': card.time_created,
        'time_updated': card.time_updated,
        'updated_by_id': card.updated_by_id
    } for card in cards]

    return jsonify(cards_list), 200

# Update Card Endpoint
@jwt_required()
def update_card(card_id):
    """Users can only update cards that they are subscribed to the group of"""

    data = request.get_json()
    user_id = get_jwt_identity()
    user_uuid = UUID(user_id)

    card = Card.query.filter_by(card_id=card_id).first()
    if not card:
        return jsonify({'message': 'Card not found'}), 404

    # Check that the user is subscribed to the group of the card
    user = User.query.filter_by(id=user_uuid).first()
    user_groups = user.subscribed_groups.all()
    if card.group_id not in [group.group_id for group in user_groups]:
        return jsonify({'message': 'User is not subscribed to the group'}), 403

    # Update fields
    card.question = data.get('question', card.question)
    card.correct_answer = data.get('correct_answer', card.correct_answer)
    card.incorrect_answer = data.get('incorrect_answer', card.incorrect_answer)
    card.updated_by_id = user_uuid
    db.session.commit()

    return jsonify({'message': 'Card updated'}), 200

# Delete Card Endpoint
@jwt_required()
def delete_card(card_id):
    """Users can only delete cards that they are subscribed to the group of"""
    user_id = get_jwt_identity()
    user_uuid = UUID(user_id)
    user = User.query.filter_by(id=user_uuid).first()
    card = Card.query.filter_by(card_id=card_id).first()

    if not card:
        return jsonify({'message': 'Card not found'}), 404

    # Check that the user has access
    user_groups = user.subscribed_groups.all()
    if card.group_id not in [group.group_id for group in user_groups]:
        return jsonify({'message': 'User is not subscribed to the group'}), 403

    db.session.delete(card)
    db.session.commit()

    return jsonify({'message': 'Card deleted'}), 200