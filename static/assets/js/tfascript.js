/* 
*  main javascript file for theatrical_fundraiser_webapp.py
*/

function displayAssignField(event) {
    document.getElementById("assign_button").style.visibility = 'collapse';
    let newForm = document.createElement('form');
    newForm.method = "POST";
    let newFormInnerHTML = `
        <label for="character_name">Choose a character:</label>
        <div class="input-wrapper"><div class="field-12">
        <select name="character" id="character_name">`
    Object.keys(availableCharacters).forEach((play)=>{
        newFormInnerHTML += `<optgroup label="${play}">`;
        availableCharacters[play].forEach((char)=>{ newFormInnerHTML += `<option>${char}</option>`; })
        newFormInnerHTML += `</optgroup>`;
    })
    newFormInnerHTML += `
        </select></div></div>
        <input type="submit" value="Accept" class="bigredbutton">`;
    newForm.innerHTML = newFormInnerHTML;
    document.querySelector("div.container").append(newForm);
    document.getElementById("character_name").focus();
}

function setActiveTier(event) {
    let currentActiveTier = document.querySelector('.active-tier');
    if (currentActiveTier !== event.target) {
        removeClassName(currentActiveTier, 'active-tier')
        addClassName(event.target, 'active-tier')
        document.getElementById('donation-entry').setAttribute('value', event.target.innerText)
        document.getElementById('current-tier').setAttribute('value', event.target.id) }
}

function removeClassName(element, name) {
    let classes = element.className.split(' ');
    element.className = classes.filter((className)=>{className !== name}).join(' ');
}

function addClassName(element, name) {
    let classes = element.className.split(' ');
    classes.push(name)
    element.className = classes.join(' ');
}

function intToDollarString(amount) {
    let dollars = amount.toString();
    let i = 3;
    while ( i < dollars.length ) {
        dollars = dollars.slice(0, -i)+','+dollars.slice(-i);
        i += 4;
    }
    dollars = '$'+dollars;
    return dollars;
}

function donorTableClick(event) {
    let donorname = event.target.parentNode.children[0].innerText;
    let data = new FormData();
    data.append( "donorname", donorname );
    fetch("/find", { method: "POST", body: data, })
        .then((response) => { if (response.redirected) window.location = response.url; })
}

function makeChart(canvas) {
    let plays = Object.keys(playData);
    let colors = plays.map( (play) => playData[play]['color'] )
    // let bkgColors = colors.map( (color) => color+"55" )  // set bar color alpha to 33%
    let amounts = plays.map( (play) => playData[play]['amount'] )
    let highestPledge = Math.max(...amounts)
    let graphMax = ( highestPledge > 1000 ) ? highestPledge : 1000
    // let idx = amounts.indexOf(highestPledge)             // Get index of highest amount
    // bkgColors[idx] = bkgColors[idx].slice(0,8)+"AA"      // then set that bar to opaque (66% alpha)
    let total = amounts.reduce((sum,amt)=>sum+=amt);
    document.querySelector('#pledge-totals > h1').innerText = intToDollarString(total);
    let chartConfig = {
        type: 'bar',
        data: {
            labels: plays,
            datasets: [ {
                label: "Pledged So Far:",
                data: amounts,
                backgroundColor: colors,
                //backgroundColor: bkgColors,
                //borderColor: colors,
                borderWidth: 0,
            } ],
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            barThickness: 32,
            borderRadius: 8,
            animation: false,
            scales: {
                x: { 
                    grid: {display: false,},
                    max: graphMax
                },
                y: { grid: {display: false,} },
            },
            plugins: {
                legend: {display: false,}
            },
        },
        grid: { display: false, },
    };
    return new Chart(canvas, chartConfig);
}

async function updateChart(chart) {
    try {
    const response = await fetch("/chart/update");
        if (response.ok) {
            const playData = await response.json();
            let plays = Object.keys(playData);
            let colors = plays.map( play=>playData[play]['color'] );
            let amounts = plays.map( play=>playData[play]['amount'] );
            let highestPledge = Math.max(...amounts);
            let total = amounts.reduce((sum,amt)=>sum+=amt);
            chart.data.labels = plays;
            chart.data.datasets[0].data = amounts;
            chart.data.datasets[0].backgroundColor = colors;
            if (highestPledge > 1000) { chart.options.scales.x.max = highestPledge; }
            document.querySelector('#pledge-totals > h1').innerText = intToDollarString(total);
            chart.update('none');
        }
    } catch (error) {
        console.log(error);
    }
}

if (document.readyState !== "loading") {
    let page = document.querySelector('main').id;
    switch (page) {
        case 'home':
            break;
        case 'create':
            document.getElementById('fname').focus()
            break;
        case 'lookup':
            document.getElementById('dname').focus()
            break;
        case 'review':
            const assignButton = document.getElementById('assign_button')
            assignButton.addEventListener('click', displayAssignField);
            if (showAssignButton) {
                assignButton.style.visibility = 'visible';
                assignButton.focus()
            }
            break;
        case 'pledge':
            let tiers = document.querySelectorAll('.tiers > div');
            tiers.forEach((tier)=>{tier.addEventListener('click', setActiveTier);})
            if ( ! document.querySelector('.active-tier')) {
                let currentActiveTierId = document.getElementById('current-tier').getAttribute('value');
                let currentActiveTier = document.getElementById(currentActiveTierId);
                addClassName(currentActiveTier, 'active-tier');
                document.getElementById('donation-entry').setAttribute('value', document.getElementById(currentActiveTierId).innerText)
            }
            document.querySelector('.add-pledge input[name="donor-alias"]').focus()
            break;
        case 'donor-list':
            let rows = document.querySelectorAll('table.donors-list tr');
            for (let idx=1; idx<rows.length; idx++) { rows[idx].addEventListener('click', donorTableClick); }
            break;
        case 'chart':
            // console.log(playData);
            const chartCanvas = document.getElementById('donations_by_show');
            const playChart = makeChart(chartCanvas);
            const timer = setInterval(updateChart, 1000, playChart);
            break;
    }
}