export type Runner = {
  id:number; number:number; horse_name:string; age?:number|null; sex?:string|null;
  weight_kg?:number|null; draw?:number|null; handicap_value?:number|null;
  record_km_seconds?:number|null; ferrure?:string|null; equipment?:string|null;
  jockey_driver?:string|null; trainer?:string|null; recent_form?:string|null; scratched:boolean;
};
export type Race = {id:number;code:string;name:string;scheduled_at:string;discipline:string;distance_m?:number|null;surface?:string|null;going?:string|null;class_name?:string|null;start_type?:string|null;status:string;runners:Runner[]};
export type Meeting = {id:number;race_date:string;code:string;track:string;country?:string|null;races:Race[]};
export type Score = {number:number;horse_name:string;performance:number;placed:number;hidden_potential:number;robustness:number;uncertainty:number;line_strength:number;reasons:string[];breakdown:Record<string,unknown>};
export type Analysis = {snapshot_id:number;race_id:number;generated_at:string;methodology_version:string;locked:boolean;confirmation:string;summary:Record<string,any>;scores:Score[]};
