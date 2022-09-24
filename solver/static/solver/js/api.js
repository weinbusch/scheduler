function API(csrf_token, schedule_url){
    let days_url = schedule_url + "/days",
        preferences_url = schedule_url + "/preferences",
        assignments_url = schedule_url + "/assignments";

    this.getSchedule = function(){
        return fetch(schedule_url, {
            method: "GET",
        }).then(r => {if (r.ok) {return r.json()}})
    }
    
    this.patchSchedule = function(url){
        return fetch(url, {
            method: "PATCH",
            headers: {
                "X-CSRFToken": csrf_token,
            },            
        })
    }
    
    this.addDay = function(dateStr){
        return fetch(days_url, {
            method: "PATCH",
            headers: {
                "X-CSRFToken": csrf_token,
            },
            body: JSON.stringify({
                date: dateStr,
            }),
        })
    }

    this.removeDay = function(dateStr){
        return fetch(days_url, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": csrf_token,
            },
            body: JSON.stringify({
                date: dateStr,
            }),
        })
    }

    this.addPreference = function(name, dateStr){
        return fetch(preferences_url, {
            method: "PATCH",
            headers: {
                "X-CSRFToken": csrf_token,
            },
            body: JSON.stringify({
                name: name,
                date: dateStr,
            }),
        })    
    }

    this.removePreference = function(name, dateStr){
        return fetch(preferences_url, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": csrf_token,
            },
            body: JSON.stringify({
                name: name,
                date: dateStr,
            }),
        })    
    }
}

