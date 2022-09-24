function Calendar(selector, options){
    let el = document.querySelector(selector);
    return new FullCalendar.Calendar(el, {
        initialView: "dayGridMonth",
        locale: "de",
        timeZone: "UTC",
        height: "auto",
        buttonText: {
            "today": "Heute",
        },
        initialDate: options.initialDate,
        eventSources: options.eventSources,
        eventClick: options.eventClick ? _.debounce(options.eventClick, 200) : undefined,
        dateClick: options.dateClick ? _.debounce(options.dateClick, 200) : undefined,
    })
}

function AssignmentCalendar(selector, options){
    let api = options.api;

    options.eventSources = [{
        events: function(info, success, failure){
            api.getSchedule().then(json => {
                let events = [];
                json.assignments.forEach(day => {
                    events.push({
                        start: day.start,
                        title: day.participant,
                        classNames: "p-2",
                    })
                });
                json.days.forEach(day => {
                    events.push({
                        start: day.start,
                        display: "background",
                    })
                })
                return success(events);
            })
        }
    }]
    
    return Calendar(selector, options);
}

function DayCalendar(selector, options){
    let api = options.api;

    options.eventSources = [{
        events: function(info, success, failure){
            api.getSchedule().then(json => {
                let events = [];
                json.days.forEach(day => {
                    events.push({
                        start: day.start,
                        display: "background",
                    })
                })
                return success(events);
            })
        }
    }]

    options.eventClick = function(info){
        let dateStr = info.event.startStr;
        api.removeDay(dateStr).then(
            r => {if (r.ok){ this.refetchEvents() }}
        )
    }

    options.dateClick = function(info){
        let dateStr = info.dateStr;
        if (this.getEvents().filter(e => e.startStr == dateStr).length){
            return;
        }
        api.addDay(dateStr).then(
            r => {if (r.ok) { this.refetchEvents() }}
        )
    }

    return Calendar(selector, options);
}

function ParticipantCalendar(selector, options){
    let participantSelector = document.querySelector(options.participantSelector);
    
    getSelectedParticipant = function(){
        let el = participantSelector;
        let checked = el ? el.querySelector("input:checked") : null;
        return checked ? checked.value : null;
    };
    
    let api = options.api;

    options.eventSources = [
        {
            events: function(info, success, failure){
                api.getSchedule().then(json => {
                    let days = json.days,
                        preferences = json.preferences,
                        assignments = json.assignments;
                    let events = [];
                    days.forEach(day => events.push({
                        groupId: "days",
                        start: day.start,
                        display: "background",
                    }))
                    preferences.forEach(day => events.push({
                        groupId: "preferences",
                        start: day.start,
                        participant: day.participant,
                    }))
                    return success(events);
                })
                
            },
            eventDataTransform: function(eventData){
                eventData.title = eventData.participant || "";
                if (eventData.participant == getSelectedParticipant()){
                    eventData.classNames = ["p-1", "cursor-pointer", "hover:ring"];
                } else {
                    eventData.classNames = "opacity-50"
                }
                return eventData;
            },
        },
    ],


    options.eventClick = function(info){
        let participant = info.event.extendedProps.participant,
            dateStr = info.event.startStr;
        if (participant && participant == getSelectedParticipant()){
            api.removePreference(participant, dateStr).then((r) => {if (r.ok){
                this.refetchEvents()
            }})
        }
    };

    options.dateClick = function(info){
        let participant = getSelectedParticipant(),
            dateStr = info.dateStr,
            events = this.getEvents(),
            isAvailable = events.filter(e => 
                e.startStr == dateStr && e.groupId == "days"
            ).length == 1,
            isEmpty = events.filter(e => {
                e.startStr == dateStr && e.extendedProps.participant == participant
            }).length == 0;
        if (isAvailable && isEmpty){
            api.addPreference(participant, dateStr).then(r => {
                if (r.ok){
                    this.refetchEvents()
                }
            })
        }
    };

    let calendar = Calendar(selector, options);

    if (participantSelector){
        participantSelector.addEventListener("change", ()=>calendar.refetchEvents());
    }

    return calendar;
}
