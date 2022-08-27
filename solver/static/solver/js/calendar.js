function patchSchedule(url, csrf_token){
    return fetch(url, {
        method: "PATCH",
        headers: {
            "X-CSRFToken": csrf_token,
        },
    })
}

function calendar(el, options){

    function dateString(date){
        return date.toISOString().slice(0, 10);
    }

    function canAddToDate(dateStr){
        let d = new Date(dateStr);
        return (!options.start || dateStr >= options.start) && (!options.end || dateStr <= options.end) && d.getDay() > 0 && d.getDay() < 6;
    }
    
    function getSelectedUser(){
        let el = document.getElementById("calendar_users");
        if (el){
            let checked = el.querySelector("input:checked");
            if (checked != null){
                return checked.value;
            } else {
                return null
            }
        }
    }
    
    function inactivateEvent(url){
        return fetch(url, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": options.csrf_token,
            },
        })
    }
    
    function addEvent(url, start){
        let user = getSelectedUser();
        if (user){
            return fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": options.csrf_token,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    user: getSelectedUser(),
                    start: start,
                })
            })
        } else {
            return Promise.reject("User is empty.")
        }
    }
    
    function makeCalendar(){
        let c = new FullCalendar.Calendar(el, {
            timeZone: "UTC",
            initialDate: options.start,
            locale: "de",
            buttonText: {
                "today": "Heute",
            },
            initialView: "dayGridMonth",
            events: {
                url: options.url,
            },
            eventClassNames(info){
                let u = info.event.extendedProps.user;
                if (!options.selectUser){
                    return "px-2 py-1"
                }
                else if (u == getSelectedUser()){
                    return "px-2 py-1 hover:ring"
                } else {
                    return "text-slate-100"
                }
            },
            eventClick(info){
                info.jsEvent.preventDefault();
                let selected_user = getSelectedUser(),
                    event_user = info.event.extendedProps.user;
                if (options.canDelete && selected_user == event_user){
                    inactivateEvent(info.event.url).then(r => {
                        if (r.ok) {
                            this.refetchEvents()
                        } else {
                            console.log("could not delete event", info.event.id)
                        }
                    });
                }
            },
            dateClick(info){
                // https://fullcalendar.io/docs/dateClick
                let dateStr = info.dateStr;
                if (options.canAdd && canAddToDate(dateStr)) {
                    addEvent(options.url, dateStr).then(r => {
                        if (r.ok) {
                            this.refetchEvents()
                        } else {
                            console.log("could not add event");
                        }
                    }).catch(obj => console.log(obj))
                }
            },
            eventDataTransform(data){
                data.title = data.username;
                if (options.selectUser && data.user != getSelectedUser()){
                    data.backgroundColor = "transparent";
                    data.borderColor = data.backgroundColor;
                    data.textColor = "black";
                    
                }
                return data;
            },
            dayCellClassNames(info){
                // https://fullcalendar.io/docs/day-cell-render-hooks
                let dateStr = dateString(info.date);
                if (canAddToDate(dateStr)) {
                    return "bg-sky-200/25";
                }
            },
        });
        return c;
    }
    
    function init(){
        let c = makeCalendar();
        if (options.selectUser) {
            document.getElementById("calendar_users").addEventListener("change", () => {
                c.refetchEvents();
            });
        }
        c.render();
        return c;
    }

    return init();
}

