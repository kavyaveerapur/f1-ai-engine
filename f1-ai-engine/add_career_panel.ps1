$path = "frontend\dashboard.html"

$html = Get-Content $path -Raw

$marker = '<div id="otherTeamsSection"'

if (-not $html.Contains($marker)) {
    Write-Host "ERROR: dashboard insertion point not found."
    exit 1
}

if ($html.Contains('id="careerPanel"')) {
    Write-Host "Career panel already exists. Nothing changed."
    exit 0
}

$panel = @"
<!-- =========================================================
     MY CAREER / CHAMPIONSHIP PANEL
========================================================= -->

<section id="careerPanel" class="career-panel">

    <div class="career-header">

        <div>
            <div class="career-kicker">
                2026 CHAMPIONSHIP
            </div>

            <h2>MY TEAM PERFORMANCE</h2>

            <p id="careerStatusText">
                Career ready · Round 1
            </p>
        </div>

        <button
            id="startCareerButton"
            class="career-start-btn"
            onclick="startCareer()"
        >
            START CAREER
        </button>

    </div>


    <!-- CHAMPIONSHIP SUMMARY -->

    <div class="career-stats">

        <div class="career-stat-card">

            <span>POSITION</span>

            <strong id="careerPosition">
                —
            </strong>

        </div>


        <div class="career-stat-card">

            <span>POINTS</span>

            <strong id="careerPoints">
                0
            </strong>

        </div>


        <div class="career-stat-card">

            <span>WINS</span>

            <strong id="careerWins">
                0
            </strong>

        </div>


        <div class="career-stat-card">

            <span>PODIUMS</span>

            <strong id="careerPodiums">
                0
            </strong>

        </div>

    </div>


    <!-- TEAM COMPARISON -->

    <div class="career-section">

        <div class="career-section-title">
            TEAM COMPARISON
        </div>

        <div
            id="careerTeamComparison"
            class="career-comparison-grid"
        >
            <div class="career-empty">
                Start your career to load championship data.
            </div>
        </div>

    </div>


    <!-- RACE PACE -->

    <div class="career-section">

        <div class="career-section-title">
            RACE PACE
        </div>

        <div class="pace-columns">

            <div>

                <div class="pace-title">
                    COMPLETED RACES
                </div>

                <div id="completedRacePace">

                    <div class="career-empty">
                        No completed races yet.
                    </div>

                </div>

            </div>


            <div>

                <div class="pace-title">
                    UPCOMING RACES
                </div>

                <div id="upcomingRacePace">

                    <div class="career-empty">
                        Upcoming race expectations will appear here.
                    </div>

                </div>

            </div>

        </div>

    </div>

</section>


<style>

/* =========================================================
   CAREER PANEL
========================================================= */

.career-panel {

    width: min(1180px, 92vw);

    margin: 50px auto;

    padding: 30px;

    border:
        1px solid
        rgba(255,255,255,0.10);

    border-radius: 14px;

    background:
        rgba(2,6,23,0.72);

    backdrop-filter: blur(18px);

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.35);
}


.career-header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 20px;

    margin-bottom: 25px;
}


.career-kicker {

    font-family:
        'Orbitron',
        monospace;

    font-size: 10px;

    letter-spacing: 3px;

    color:
        #e10600;

    margin-bottom: 7px;
}


.career-header h2 {

    font-family:
        'Orbitron',
        monospace;

    font-size: 22px;

    letter-spacing: 1px;
}


.career-header p {

    margin-top: 6px;

    color:
        rgba(255,255,255,0.42);

    font-size: 14px;
}


.career-start-btn {

    padding:
        13px 22px;

    border: none;

    border-radius: 6px;

    background:
        linear-gradient(
            135deg,
            #e10600,
            #a80000
        );

    color: white;

    font-family:
        'Orbitron',
        monospace;

    font-size: 11px;

    font-weight: 700;

    letter-spacing: 1.5px;

    cursor: pointer;

    transition:
        transform .2s,
        box-shadow .2s;
}


.career-start-btn:hover {

    transform:
        translateY(-2px);

    box-shadow:
        0 8px 25px
        rgba(225,6,0,0.35);
}


/* STATS */

.career-stats {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 12px;

    margin-bottom: 28px;
}


.career-stat-card {

    padding: 20px;

    border:
        1px solid
        rgba(255,255,255,0.08);

    border-radius: 8px;

    background:
        rgba(255,255,255,0.035);

    text-align: center;
}


.career-stat-card span {

    display: block;

    color:
        rgba(255,255,255,0.38);

    font-family:
        'Orbitron',
        monospace;

    font-size: 9px;

    letter-spacing: 2px;

    margin-bottom: 8px;
}


.career-stat-card strong {

    font-family:
        'Orbitron',
        monospace;

    font-size: 26px;

    color:
        #ffd700;
}


/* SECTIONS */

.career-section {

    margin-top: 28px;
}


.career-section-title {

    font-family:
        'Orbitron',
        monospace;

    font-size: 11px;

    letter-spacing: 2px;

    color:
        rgba(255,255,255,0.65);

    margin-bottom: 12px;
}


/* TEAM COMPARISON */

.career-comparison-grid {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(190px, 1fr));

    gap: 10px;
}


.career-team-card {

    padding: 15px;

    border:
        1px solid
        rgba(255,255,255,0.08);

    border-radius: 8px;

    background:
        rgba(255,255,255,0.035);

    cursor: pointer;

    transition:
        transform .2s,
        border-color .2s;
}


.career-team-card:hover {

    transform:
        translateY(-2px);

    border-color:
        rgba(255,215,0,0.35);
}


.career-team-card.mine {

    border-color:
        rgba(225,6,0,0.55);

    background:
        rgba(225,6,0,0.08);
}


.career-team-name {

    font-weight: 700;

    margin-bottom: 8px;
}


.career-team-points {

    font-family:
        'Orbitron',
        monospace;

    font-size: 18px;

    color:
        #ffd700;
}


.career-team-gap {

    margin-top: 6px;

    font-size: 12px;

    color:
        rgba(255,255,255,0.45);
}


/* PACE */

.pace-columns {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 18px;
}


.pace-title {

    font-family:
        'Orbitron',
        monospace;

    font-size: 9px;

    letter-spacing: 2px;

    color:
        rgba(255,255,255,0.38);

    margin-bottom: 9px;
}


.pace-row {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 10px;

    padding: 12px 14px;

    margin-bottom: 7px;

    border:
        1px solid
        rgba(255,255,255,0.07);

    border-radius: 7px;

    background:
        rgba(255,255,255,0.025);
}


.pace-circuit {

    font-weight: 600;
}


.pace-result {

    font-family:
        'Orbitron',
        monospace;

    font-size: 10px;

    color:
        rgba(255,255,255,0.65);
}


.pace-faster {

    color:
        #5ee7a1;
}


.pace-slower {

    color:
        #ff7777;
}


.pace-close {

    color:
        #ffd700;
}


.career-empty {

    padding: 18px;

    border:
        1px dashed
        rgba(255,255,255,0.10);

    border-radius: 7px;

    color:
        rgba(255,255,255,0.30);

    font-size: 13px;
}


@media (max-width: 700px) {

    .career-header {

        flex-direction: column;

        align-items: flex-start;
    }

    .career-stats {

        grid-template-columns:
            repeat(2, 1fr);
    }

    .pace-columns {

        grid-template-columns: 1fr;
    }

}

</style>

"@

$html = $html.Replace(
    $marker,
    $panel + "`r`n`r`n" + $marker
)

Set-Content $path $html

Write-Host "Career panel added successfully."
