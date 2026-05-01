gsap.registerPlugin(ScrollTrigger)

const data = [
    {
        small: "Feature 01",
        title: "Players",
        desc: `Voxlytics provides beautiful stat profiles for all players on the Voxyl Network. 
    Use <span class="command">/stats [player] [mode]</span> to view detailed in-game statistics. 
    Link your account with <span class="command">/link [player]</span> to make running commands faster and easier.`,
        img: "/static/images/player.png"
    },
    {
        small: "Feature 02",
        title: "Leaderboards",
        desc: `Voxlytics lets you explore competitive leaderboards across the Voxyl Network. 
    Use <span class="command">/leaderboard level [page]</span> or 
    <span class="command">/leaderboard weightedwins [page]</span> to browse rankings.`,
        img: "/static/images/leaderboard.png"
    },
    {
        small: "Feature 03",
        title: "Historical",
        desc: `Voxlytics includes historical tracking, allowing you to view player progress over time. 
    Use <span class="command">/historical daily [player]</span>, 
    <span class="command">/historical weekly [player]</span>, 
    <span class="command">/historical monthly [player]</span>, or 
    <span class="command">/historical yearly [player]</span> to track stats across different time periods. 
    You can reset your historical data with <span class="command">/historical reset</span>.`,
        img: "/static/images/historical.png"
    },
    {
        small: "Feature 04",
        title: "Sessions",
        desc: `Voxlytics sessions let you track your progress in real time across play sessions. 
    Each user can have only one active session, and you must be linked to create or view session data. 
    Use <span class="command">/session view [player]</span> to see your current session stats, or 
    <span class="command">/session reset</span> to clear your session and start fresh.`,
        img: "/static/images/session.png"
    },
    {
        small: "Feature 05",
        title: "Projected",
        desc: `Voxlytics Prestige allows you to project a player's future stats based on their session stats. 
    Use <span class="command">/prestige <level> [player]</span> to calculate estimated progression and stat outcomes from an active session. 
    A session must be started first using <span class="command">/session view</span> before prestige data can be generated.`,
        img: "/static/images/projected.png"
    },
    {
        small: "Feature 06",
        title: "Compare",
        desc: `Voxlytics lets you compare player stats side by side to see who comes out on top. 
    Use <span class="command">/compare [player_1] [player_2]</span> to instantly view a detailed comparison of their stats.`,
        img: "/static/images/compare.png"
    },
    {
        small: "Feature 07",
        title: "Milestones",
        desc: `Voxlytics lets you track milestones and get notified when you're close to reaching them. 
        Use <span class="command">/milestone add [type] [threshold]</span> to create one, 
        <span class="command">/milestone remove</span> to delete, and 
        <span class="command">/milestone view</span> to see your milestones.`,
        img: "/static/images/milestones.png"
    },
    {
        small: "Feature 08",
        title: "Live Updates",
        desc: `Voxlytics allows live leaderboard updates directly in your server. 
    Use <span class="command">/updated [channel]</span> to enable real-time level and weighted wins leaderboard updates.`,
        img: "/static/images/leaderboard_updates.png"
    },
    {
        small: "Feature 09",
        title: "Guild Tracking",
        desc: `Voxlytics lets you track guild activity and performance. 
    Use <span class="command">/tracker config [charts]</span> to enable tracking, then 
    <span class="command">/tracker add [tag] [logs_channel]</span> to add a guild. 
    Track joins, leaves, weekly stats, and XP charts that reset every Monday.`,
        img: "/static/images/guildtracking.png"
    }
]

const small = document.getElementById("feature-small")
const title = document.getElementById("feature-title")
const desc = document.getElementById("feature-desc")
const img = document.getElementById("feature-img")

let current = 0

function animate(direction) {
    gsap.fromTo(".feature-text",
        { x: direction > 0 ? -200 : 200, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }
    )

    gsap.fromTo(".feature-image",
        { x: direction > 0 ? 200 : -200, opacity: 0, scale: 0.9 },
        { x: 0, opacity: 1, scale: 1, duration: 0.6, ease: "power3.out" }
    )
}

ScrollTrigger.create({
    trigger: ".feature-scroll",
    start: "top top",
    end: "bottom bottom",
    scrub: 0.6,
    onUpdate: self => {
        const progress = self.progress
        const step = Math.round(progress * (data.length - 1))

        if (step !== current) {
            const direction = step > current ? 1 : -1
            current = step

            small.textContent = data[step].small
            title.textContent = data[step].title
            desc.innerHTML = data[step].desc
            img.src = data[step].img

            animate(direction)
        }
    }
})

animate(1)