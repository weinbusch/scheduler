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
