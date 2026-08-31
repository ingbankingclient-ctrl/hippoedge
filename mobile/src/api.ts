import AsyncStorage from '@react-native-async-storage/async-storage';
import type {Meeting,Analysis} from './types';

const KEY='hippoedge_api_url';
export async function getBaseUrl(){return (await AsyncStorage.getItem(KEY)) || 'http://127.0.0.1:8000';}
export async function setBaseUrl(v:string){await AsyncStorage.setItem(KEY,v.replace(/\/$/,''));}
async function req<T>(path:string, init?:RequestInit):Promise<T>{
  const base=await getBaseUrl();
  const r=await fetch(base+path,{...init,headers:{'Content-Type':'application/json',...(init?.headers||{})}});
  if(!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
export const Api={
  tomorrow:()=>req<Meeting[]>('/api/tomorrow'),
  program:(day:string)=>req<Meeting[]>(`/api/program/${day}`),
  refresh:(day:string)=>req<any>(`/api/refresh?day=${day}`,{method:'POST'}),
  analysis:(id:number,force=false)=>req<Analysis>(`/api/races/${id}/analysis?force=${force}`),
  lock:(id:number)=>req<any>(`/api/races/${id}/lock`,{method:'POST'}),
  stats:()=>req<any>('/api/stats'),
  health:()=>req<any>('/health')
};
