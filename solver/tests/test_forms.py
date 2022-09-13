import pytest

from solver.forms import ParticipantForm


def test_participant_form_is_invalid_if_participant_already_exists():
    form = ParticipantForm({"name": "foo"}, participants={"foo", "bar", "baz"})
    assert form.is_valid() is False


def test_participant_form_requires_name():
    form = ParticipantForm({"name": ""}, participants={"foo"})
    assert form.is_valid() is False


def test_participant_form_is_valid():
    form = ParticipantForm({"name": "foobar"}, participants={"foo", "bar", "baz"})
    assert form.is_valid()


def test_participant_form_weekdays():
    form = ParticipantForm(participants={"foo"})
    assert form["weekdays"].field.choices == [
        (0, "montags"),
        (1, "dienstags"),
        (2, "mittwochs"),
        (3, "donnerstags"),
        (4, "freitags"),
        (5, "samstags"),
        (6, "sonntags"),
    ]


def test_participant_form_validates_weekday():
    form = ParticipantForm({"name": "foo", "weekdays": [1, 2, 4]}, participants={})
    assert form.is_valid()
    assert form.cleaned_data["weekdays"] == [1, 2, 4]


@pytest.mark.parametrize("input", ["foo", 7])
def test_participant_form_handles_invalid_weekdays(input):
    form = ParticipantForm({"name": "foo", "weekdays": [input]}, participants={})
    assert form.is_valid() is False
