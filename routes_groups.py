"""Private groups: create/join by invite code, view members + portfolios +
a performance leaderboard, and a simple discussion thread."""

import random
import string

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from forms import GroupForm, GroupInviteForm, GroupJoinForm, GroupMessageForm
from models import Group, GroupMembership, GroupMessage, User
from prices import attach_stats


def _generate_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(alphabet, k=6))
        if not Group.query.filter_by(code=code).first():
            return code


@login_required
def groups_home():
    groups = [m.group for m in current_user.group_memberships]
    return render_template("groups_home.html", groups=groups, join_form=GroupJoinForm())


@login_required
def group_new():
    form = GroupForm()
    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            description=form.description.data,
            code=_generate_code(),
            owner_id=current_user.id,
        )
        db.session.add(group)
        db.session.flush()
        db.session.add(GroupMembership(group_id=group.id, user_id=current_user.id))
        db.session.commit()
        flash(f"Group created — invite code: {group.code}", "success")
        return redirect(url_for("group_detail", group_id=group.id))

    return render_template("group_form.html", form=form)


@login_required
def group_join():
    form = GroupJoinForm()
    if form.validate_on_submit():
        group = Group.query.filter_by(code=form.code.data).first()
        if group is None:
            flash("No group found with that invite code.", "error")
        elif group.has_member(current_user):
            flash("You're already in that group.", "error")
        else:
            db.session.add(GroupMembership(group_id=group.id, user_id=current_user.id))
            db.session.commit()
            flash(f"Joined {group.name}.", "success")
            return redirect(url_for("group_detail", group_id=group.id))

    groups = [m.group for m in current_user.group_memberships]
    return render_template("groups_home.html", groups=groups, join_form=form)


@login_required
def group_detail(group_id):
    group = db.session.get(Group, group_id)
    if group is None:
        abort(404)
    if not group.has_member(current_user):
        abort(403)

    members = group.members
    portfolios = [m.portfolio for m in members if m.portfolio is not None]
    attach_stats(portfolios)
    leaderboard = sorted(
        (p for p in portfolios if p.stats.get("total_gain_loss_pct") is not None),
        key=lambda p: p.stats["total_gain_loss_pct"],
        reverse=True,
    )

    invite_form = GroupInviteForm()
    message_form = GroupMessageForm()
    if message_form.validate_on_submit():
        db.session.add(
            GroupMessage(group_id=group.id, user_id=current_user.id, body=message_form.body.data)
        )
        db.session.commit()
        return redirect(url_for("group_detail", group_id=group.id))

    return render_template(
        "group_detail.html",
        group=group,
        members=members,
        leaderboard=leaderboard,
        invite_form=invite_form,
        message_form=message_form,
    )


@login_required
def group_invite(group_id):
    group = db.session.get(Group, group_id)
    if group is None:
        abort(404)
    if group.owner_id != current_user.id:
        abort(403)

    form = GroupInviteForm()
    if form.validate_on_submit():
        target = User.query.filter_by(username=form.username.data).first()
        if target is None:
            flash("No user with that username.", "error")
        elif group.has_member(target):
            flash(f"{target.username} is already in this group.", "error")
        else:
            db.session.add(GroupMembership(group_id=group.id, user_id=target.id))
            db.session.commit()
            flash(f"Added {target.username} to {group.name}.", "success")

    return redirect(url_for("group_detail", group_id=group.id))


def register(app):
    app.add_url_rule("/groups", view_func=groups_home)
    app.add_url_rule("/groups/new", view_func=group_new, methods=["GET", "POST"])
    app.add_url_rule("/groups/join", view_func=group_join, methods=["GET", "POST"])
    app.add_url_rule(
        "/groups/<int:group_id>", view_func=group_detail, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/groups/<int:group_id>/invite", view_func=group_invite, methods=["POST"]
    )
