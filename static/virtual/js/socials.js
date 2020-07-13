const start = (social_json_path) => {
    d3.json(social_json_path).then(social_all => {

        console.log(social_all, "--- social_all");

        d3.select("#socials_content")
          .html(() => social_all.filter(d => d.type === 'social')
            .map(socials_template).join('\n'))

        d3.select("#mentors_content")
          .html(() => social_all.filter(d => d.type !== 'social')
            .map(socials_template).join('\n'))

        // d3.select("#all_socials")
        //   .selectAll('.a_social').data(social_all)
        //   .enter().append(event=> socials_template(event))


    })
}


const sessions = event => {
    return event.sessions.map(s =>
      `<p>  
        <span class="session_times"> ${s.time}</span> 
        [<a href="${s.link}" target="_blank">Live Zoom</a>] 
        </p>`)
      .join(' ')
}

function imageExists(image_url) {

    const http = new XMLHttpRequest();

    http.open('HEAD', image_url, false);
    http.send();

    return http.status != 404;

}

function image(event) {
    const cleanTitle = event.title.replace(':', '-').replace('?', '_')
    const link = `/static/virtual/img/social_thumbnails/${cleanTitle}.png`

    if (imageExists(link)) {
        return `<img src="${link}" style="max-width: 100%; height: auto;max-height: 100px;" >`
    } else {
        return `<img height="100" src="/static/virtual/img/social_thumbnails/ICML_social_temp.png" >`
    }


}

function chat_part(event) {
    if (event.chat !== '')
        return `<p class="text-center text-muted card-title">
     <a href="${event.chat}" target="_blank"> TextChat </a>
     </p>`
    else
        return ''
}

const socials_template = (event) => `
 <div class="col-lg-4 col-md-6 col-sm-12 p-3 a_social"
             id='${event.title.replace(" ", "_").replace("?", "")}'
             style="box-sizing: border-box;">
            <div class="card"
                 style="display:block; overflow:hidden; width:100%;">
                <div class="card-header text-center"
                     style="min-height: 400px; width:100%;">
<!--                    <a class="text-muted" href="#">-->
                        <h3 class="card-title">
                            ${event.title}
                        </h3>
<!--                    </a>-->
<!--                    <div class="card-subtitle text-muted">-->
<!--                        {{social.organizers}}-->
<!--                    </div>-->
                    <div class="m-4">
                        ${image(event)}
                        
<!--                        <img height="100"-->
<!--                             src="https://iclr.github.io/iclr-images/socials/ICLR_social_temp.png"/>-->
                    </div>
                    <div class="p-3 text-left card-subtitle text-muted">

                        <div style="height: 150px; overflow-y: auto;">
                                                <p>${event.description}</p>
                        </div>
                        <br/>
                        <div class="text-center text-muted text-monospace">
                            ${sessions(event)}
                        
                        </div>
                        ${chat_part(event)}
                        
<!--                        <p class="text-center text-muted card-title">-->
<!--                            <a href="chat.html?room=channel/social_{{social.id}}" target="_blank"> Chat </a>-->
<!--                            {% if social.website %}-->
<!--                            | <a href="{{social.website}}" target="_blank"> Website </a>-->
<!--                            {% endif %}-->
<!--&lt;!&ndash;                            {% if social.links %}&ndash;&gt;-->
<!--&lt;!&ndash;                            {% for l in social.links %}&ndash;&gt;-->
<!--&lt;!&ndash;                            | <a href="{{l}}" target="_blank"> Live ({{social.day[loop.index-1]}}) </a>&ndash;&gt;-->
<!--&lt;!&ndash;                            {% endfor %}&ndash;&gt;-->
<!--&lt;!&ndash;                            {% endif %}&ndash;&gt;-->


<!--                        </p>-->

                    </div>

                </div>
            </div>
        </div>
  `
