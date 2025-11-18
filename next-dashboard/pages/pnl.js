import useSWR from "swr";
const fetcher = (url) => fetch(url).then(r=>r.json());
export default function Pnl(){
  const {data} = useSWR("http://localhost:7000/pnl/summary", fetcher, {refreshInterval:5000});
  return <div style={{padding:20}}><h2>PnL</h2><pre>{JSON.stringify(data,null,2)}</pre></div>
}
