from flask import request, jsonify
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from datetime import datetime
import uuid

from data_imports.google_sheets import sync_cards_from_sheet

from database.db_interface import db
from database.db_types import Group, SheetSyncJob, User

from scheduler import scheduler

# Create Card Group Endpoint
@jwt_required()
def create_group():
    data = request.get_json()
    user_id = get_jwt_identity()

    # convert string to UUID
    user_uuid = uuid.UUID(user_id)

    new_group = Group(
        creator_id=user_uuid,
        group_name=data.get('group_name')
    )

    # Subscribe the user to the new group
    user = User.query.filter_by(id=user_uuid).first()
    new_group.subscribers.append(user)

    db.session.add(new_group)
    db.session.commit()

    return jsonify({'group_id': new_group.group_id}), 201

# Get Card Groups Endpoint
@jwt_required()
def get_groups():
    groups = Group.query.all()
    groups_list = [{
        'group_name': group.group_name,
        'group_id': group.group_id,
        'creator_id': group.creator_id,
        'time_created': group.time_created,
        'time_updated': group.time_updated,
        "subscribers": [subscriber.id for subscriber in group.subscribers]
    } for group in groups]
    return jsonify(groups_list), 200


# Update Card Group Endpoint
@jwt_required()
def update_group(group_id):
    data = request.get_json()
    user_id = get_jwt_identity()

    group = Group.query.filter_by(group_id=group_id).first()
    if not group:
        return jsonify({'message': 'Group not found'}), 404

    # Check that the user is the creator of the group
    if group.creator_id != uuid.UUID(user_id):
        return jsonify({'message': 'User is not the creator of the group'}), 403

    # Update fields
    group.group_name = data.get('group_name', group.group_name)

    group.time_updated = datetime.now().isoformat()
    db.session.commit()

    return jsonify({'message': 'Group updated'}), 200

# Delete Card Group Endpoint
@jwt_required()
def delete_group(group_id):
    user_id = get_jwt_identity()

    group = Group.query.filter_by(group_id=group_id).first()
    if not group:
        return jsonify({'message': 'Group not found'}), 404

    # Check that the user is the creator of the group
    if group.creator_id != uuid.UUID(user_id):
        return jsonify({'message': 'User is not the creator of the group'}), 403

    db.session.delete(group)
    db.session.commit()

    return jsonify({'message': 'Group deleted'}), 200

# Add user to group
@jwt_required()
def add_user_to_group(group_id):
    user_id = get_jwt_identity()
    user_uuid = uuid.UUID(user_id)

    group = Group.query.filter_by(group_id=group_id).first()
    if not group:
        return jsonify({'message': 'Group not found'}), 404

    user = User.query.filter_by(id=user_uuid).first()
    group.subscribers.append(user)

    db.session.commit()

    return jsonify({'message': 'User added to group'}), 200

# Get cards in group
@jwt_required()
def get_group_cards(group_id):
    group = Group.query.filter_by(group_id=group_id).first()
    if not group:
        return jsonify({'message': 'Group not found'}), 404

    cards = group.cards
    cards_list = [{
        'card_id': card.card_id,
        'question': card.question,
        'correct_answer': card.correct_answer,
        'time_created': card.time_created,
        'time_updated': card.time_updated
    } for card in cards]

    return jsonify(cards_list), 200

# Get group information
@jwt_required()
def get_group_info(group_id):
    group = Group.query.filter_by(group_id=group_id).first()
    if not group:
        return jsonify({'message': 'Group not found'}), 404

    return jsonify({
        'group_name': group.group_name,
        'group_id': group.group_id,
        'creator_id': group.creator_id,
        'time_created': group.time_created,
        'time_updated': group.time_updated
    }), 200

@jwt_required()
def create_group_from_google_sheet():
    data = request.get_json()
    group_name = data.get("group_name")
    sheet_id = data.get("sheet_id")
    sheet_range = data.get("sheet_range")

    if not (group_name and sheet_id and sheet_range):
        return jsonify({"message": "Missing required fields"}), 400

    user_id = get_jwt_identity()
    user_uuid = uuid.UUID(user_id)

    group = Group.query.filter_by(group_name=group_name).first()
    if group:
        return jsonify({"message": "Group name already exists"}), 403

    # Create a new group
    group = Group(
        creator_id=user_uuid,
        group_name=group_name
    )
    db.session.add(group)
    db.session.commit()

    # Create a new sync job (store in DB)
    new_job = SheetSyncJob(
        group_id=group.group_id,
        sheet_id=sheet_id,
        sheet_range=sheet_range,
        creator_id=user_uuid,
        cron_string="*/5 * * * *" # every 5 minutes
    )
    db.session.add(new_job)
    db.session.commit()

    # # Schedule the actual job in APScheduler
    # scheduler.add_job(
    #     id=new_job.job_id,
    #     func=sync_cards_from_sheet,
    #     args=[new_job.job_id],
    #     trigger='cron',  # or 'interval'
    #     # TODO: parse `cron_string`
    #     minute='*/5',
    # )

    return jsonify({
        "message": f"Sync job created for group: {group_name}",
        "groupd_id": group.group_id,
        "job_id": new_job.job_id
    }), 201
