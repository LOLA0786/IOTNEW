import { useEffect, useState } from "react";

export default function Home() {
  const [events, setEvents] = useState([]);
  const [symbols, setSymbols] = useState("AAPL,NVDA,MSFT");
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:7000/ws/events");
    ws.onopen = () => console.log("ws open");
    ws.onmessage = (e) => {
      try {
        const obj = JSON.parse(e.data);
        setEvents(prev => [obj, ...prev].slice(0,200));
      } catch {}
    };
    ws.onclose = () => console.log("ws closed");
    return () => ws.close();
  }, []);

  async function runMulti() {
    const res = await fetch("http://localhost:7000/run-multi", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({symbols: symbols.split(",").map(s=>s.trim())})
    });
    const j = await res.json();
    alert("ran: " + (j.count || 0));
  }

  return (
    <div style={{padding:20,fontFamily:"system-ui"}}>
      <h1>IOA Next Dashboard</h1>
      <div>
        <input style={{width:400}} value={symbols} onChange={(e)=>setSymbols(e.target.value)} />
        <button onClick={runMulti} style={{marginLeft:8}}>Run Multi</button>
      </div>
      <h3>Live Events</h3>
      <div style={{background:"#111",color:"#0f0",padding:10,height:400,overflow:"auto"}}>
        {events.map((ev,idx)=>(
          <div key={idx} style={{marginBottom:8,borderBottom:"1px solid #222",paddingBottom:6}}>
            <div><strong>{ev.symbol}</strong> {ev.decision} score={ev.score} boosted={ev.boosted}</div>
            <div style={{fontSize:12,color:"#ccc"}}>{ev.reason}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
