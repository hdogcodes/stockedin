"""Direct messages — restricted to users who mutually follow each other."""

from datetime import datetime

from flask import abort, render_template
from flask_login import current_user, login_required
from sqlalchemy import and_, or_

from extensions import db
from forms import MessageForm
from models import Message, User


def _thread_query(user_a_id, user_b_id):
    return Message.query.filter(
        or_(
            and_(Message.sender_id == user_a_id, Message.recipient_id == user_b_id),
            and_(Message.sender_id == user_b_id, Message.recipient_id == user_a_id),
        )
    )


def _build_threads():
    friends = current_user.mutual_friends
    threads = []
    for friend in friends:
        last_message = (
            _thread_query(current_user.id, friend.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        unread_count = Message.query.filter_by(
            sender_id=friend.id, recipient_id=current_user.id, read_at=None
        ).count()
        threads.append(
            {"friend": friend, "last_message": last_message, "unread_count": unread_count}
        )

    # Conversations with the most recent activity first; friends with no
    # messages yet (last_message is None) sort to the bottom.
    threads.sort(
        key=lambda t: t["last_message"].created_at if t["last_message"] else datetime.min,
        reverse=True,
    )
    return threads


@login_required
def inbox():
    return render_template("messages_inbox.html", threads=_build_threads(), active_username=None)


@login_required
def thread(username):
    target = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_mutual_with(target):
        abort(403)

    form = MessageForm()
    if form.validate_on_submit():
        db.session.add(
            Message(sender_id=current_user.id, recipient_id=target.id, body=form.body.data)
        )
        db.session.commit()
        form.body.data = ""

    _thread_query(current_user.id, target.id).filter(
        Message.sender_id == target.id, Message.read_at.is_(None)
    ).update({"read_at": datetime.utcnow()}, synchronize_session=False)
    db.session.commit()

    messages = _thread_query(current_user.id, target.id).order_by(Message.created_at).all()

    return render_template(
        "messages_thread.html",
        target=target,
        messages=messages,
        form=form,
        threads=_build_threads(),
        active_username=target.username,
    )


def register(app):
    app.add_url_rule("/messages", view_func=inbox)
    app.add_url_rule("/messages/<username>", view_func=thread, methods=["GET", "POST"])
