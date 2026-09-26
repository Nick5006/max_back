from apihandler.models import Vote, UserApartment

def get_user_domik_ids(user):
    return (
        UserApartment.objects
        .filter(user=user)
        .values_list("apartment__domik_id", flat=True)
        .distinct()
    )


def serialize_poll_choice(choice, user_vote_choice_id=None):
    votes_count = getattr(choice, "votes_count", None)
    if votes_count is None:
        votes_count = choice.votes.count()

    return {
        "id": str(choice.id),
        "text": choice.text,
        "order": choice.order,
        "votes_count": votes_count,
        "is_user_choice": (
            user_vote_choice_id is not None
            and choice.id == user_vote_choice_id
        ),
    }


def serialize_poll(poll, request=None, with_choices=True):
    data = {
        "id": str(poll.id),
        "title": poll.title,
        "description": poll.description,
        "is_active": poll.is_active,
        "created_at": poll.created_at,
        "author": {
            "id": str(poll.author.id),
            "name": poll.author.name,
            "last_name": poll.author.last_name,
        },
        "domik": {
            "id": str(poll.domik.id),
            "address": poll.domik.address,
        },
        "total_votes": getattr(poll, "total_votes", None)
            if getattr(poll, "total_votes", None) is not None
            else poll.votes.count(),
    }

    if with_choices:
        user_vote = None
        if request is not None and request.user.is_authenticated:
            user_vote = (
                Vote.objects
                .filter(poll=poll, user=request.user)
                .values_list("choice_id", flat=True)
                .first()
            )

        data["choices"] = [
            serialize_poll_choice(c, user_vote) for c in poll.choices.all()
        ]
        data["user_voted"] = user_vote is not None
        data["user_choice_id"] = str(user_vote) if user_vote else None

    return data