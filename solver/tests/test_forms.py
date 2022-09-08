from solver.forms import ParticipantForm


def test_participant_form_is_invalid():
    form = ParticipantForm({"name": "foo"}, participants={"foo", "bar", "baz"})
    assert form.is_valid() is False


def test_participant_form_is_valid():
    form = ParticipantForm({"name": "foobar"}, participants={"foo", "bar", "baz"})
    assert form.is_valid()
