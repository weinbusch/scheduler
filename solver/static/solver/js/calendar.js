function patchSchedule(url, csrf_token){
    return fetch(url, {
        method: "PATCH",
        headers: {
            "X-CSRFToken": csrf_token,
        },
    })
}

function calendar(el, options){

    options.start = options.start ? new Date(options.start) : null;
    options.end = options.end ? new Date(options.end) : null;

    function sameDate(x, y){
        return x.toISOString().slice(0, 10) == y.toISOString().slice(0, 10)
    }

    function dateString(x){
        return x.toISOString().slice(0, 10);
    }

    function canAddToDay(x){
        return options.canAdd && dateString(x) >= dateString(options.start) && dateString(x) <= dateString(options.end) && x.getDay() > 0 && x.getDay() < 6;
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
            return Promise.reject("User cannot be empty.")
        }
    }
    
    function makeCalendar(){
        let c = new FullCalendar.Calendar(el, {
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
                if (options.canDelete && getSelectedUser() == info.event.extendedProps.user){
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
                if (canAddToDay(info.date)) {
                    addEvent(options.url, info.dateStr).then(r => {
                        if (r.ok) {
                            this.refetchEvents()
                        } else {
                            console.log("could not add event");
                        }
                    })
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
                if (info.date.toISOString().slice(0, 10) > options.start.toISOString().slice(0, 10) && info.date.toISOString().slice(0, 10) < options.end.toISOString().slice(0, 10)){
                    return "bg-sky-200/25";
                }
                else if (sameDate(info.date, options.start)){
                    return "bg-green-400/25";
                }
                else if (sameDate(info.date, options.end)){
                    return "bg-red-400/25";
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

