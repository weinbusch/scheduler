function API(days_url, preferences_url, assignments_url, csrf_token){
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

