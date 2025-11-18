import useSWR from "swr";
const fetcher = (url) => fetch(url).then(r=>r.json());
export default function Portfolio(){
  const {data} = useSWR("http://localhost:7000/portfolio/positions", fetcher, {refreshInterval:5000});
  return <div style={{padding:20}}><h2>Positions</h2><pre>{JSON.stringify(data,null,2)}</pre></div>
}
