function calendar(el, options){
    function getSelectedUser(){
        return document.getElementById("calendar_users").querySelector("input:checked").value;
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
                user: this.getSelectedUser(),
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
            eventClick(info){
                info.jsEvent.preventDefault();
                inactivateEvent(info.event.url).then(r => {
                    if (r.ok) {
                        this.refetchEvents()
                    } else {
                        console.log("could not delete event", info.event.id)
                    }
                });
            },
            dateClick(info){
                addEvent(options.url, info.dateStr).then(r => {
                    if (r.ok) {
                        this.refetchEvents()
                    } else {
                        console.log("could not add event", info)
                    }
                })
            },
            eventDataTransform(data){
                data.title = data.username;
                if (data.user != getSelectedUser()){
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
        document.getElementById("calendar_users").addEventListener("change", () => {
            c.refetchEvents();
        });
        c.render();
    }

    init();
}

