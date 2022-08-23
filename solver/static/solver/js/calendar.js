function patchSchedule(url, csrf_token){
    return fetch(url, {
        method: "PATCH",
        headers: {
            "X-CSRFToken": csrf_token,
        },
    })
}

function calendar(el, options){
    function getSelectedUser(){
        let el = document.getElementById("calendar_users");
        if (el){
            return el.querySelector("input:checked").value;
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
    }
    
    function makeCalendar(){
        let c = new FullCalendar.Calendar(el, {
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
                if (u == getSelectedUser()){
                    return "px-2 py-1 hover:ring"
                } else {
                    return "text-slate-100"
                }
            },
            eventClick(info){
                info.jsEvent.preventDefault();
                if (options.canDelete){
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
                if (options.canAdd && info.date.getDay() > 0 && info.date.getDay() < 6) {
                    addEvent(options.url, info.dateStr).then(r => {
                        if (r.ok) {
                            this.refetchEvents()
                        } else {
                            console.log("could not add event", info)
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
            }
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

