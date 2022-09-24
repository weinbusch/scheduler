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

function ParticipantCalendar(selector, options){
    let getSelectedParticipant = options.getSelectedParticipant;
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
                e.startStr == dateStr && e.source.id == "days"
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
    return Calendar(selector, options);
}
