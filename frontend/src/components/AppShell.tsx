import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./AppShell.css";

type IconName = "grid" | "wave" | "upload" | "bell" | "file" | "users" | "settings" | "search" | "menu" | "x" | "shield";
const paths: Record<IconName,string> = {
 grid:"M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z", wave:"M3 12h4l2-6 4 12 2-6h6", upload:"M12 16V4m0 0-4 4m4-4 4 4M5 14v5h14v-5", bell:"M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4", file:"M6 3h9l3 3v15H6zM14 3v4h4M9 12h6M9 16h6", users:"M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20M9.5 10a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm6-1a3 3 0 1 0 0-6", settings:"M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm0-5v2M12 18.5v2M3.5 12h2M18.5 12h2M5.9 5.9l1.4 1.4M16.7 16.7l1.4 1.4M18.1 5.9l-1.4 1.4M7.3 16.7l-1.4-1.4", search:"m20 20-4.5-4.5M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13Z", menu:"M4 7h16M4 12h16M4 17h16", x:"M6 6l12 12M18 6 6 18", shield:"M12 3 20 6v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"};
function Icon({name}:{name:IconName}){return <svg className="shell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]}/></svg>}
const nav=[
 ["/dashboard","Overview","grid"], ["/dashboard/analysis","Analysis","wave"], ["/dashboard/audio","Audio intake","upload"], ["/dashboard/alerts","Alerts","bell"], ["/dashboard/reports","Reports","file"],
] as const;
const admin=[["/dashboard/organization","Organization","users"],["/dashboard/settings","Settings","settings"]] as const;
export function AppShell(){
 const {user,logout}=useAuth(); const location=useLocation(); const [open,setOpen]=useState(false); const [search,setSearch]=useState("");
 useEffect(()=>setOpen(false),[location.pathname]);
 useEffect(()=>{const fn=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();document.getElementById("global-search")?.focus()}};window.addEventListener("keydown",fn);return()=>window.removeEventListener("keydown",fn)},[]);
 const name=user?.full_name??user?.email??"Analyst"; const initials=name.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]?.toUpperCase()).join("")||"VG";
 const title=location.pathname==="/dashboard"?"Overview":location.pathname.split("/").at(-1)?.replace(/-/g," ")??"Overview";
 return <div className="app-shell">
  <aside className={`app-sidebar ${open?"mobile-open":""}`}>
   <div className="shell-brand"><span className="shell-brand-mark"><Icon name="shield"/></span><span><b>VoiceGuard</b><small>Voice security</small></span><button className="mobile-close" onClick={()=>setOpen(false)}><Icon name="x"/></button></div>
   <div className="shell-org"><span className="org-avatar">{initials}</span><span><b>{name}</b><small>{user?.role??"Analyst"}</small></span></div>
   <nav className="shell-nav"><label>Workspace</label>{nav.map(([to,label,icon])=><NavLink key={to} to={to} end={to==="/dashboard"} className={({isActive})=>`shell-link ${isActive?"active":""}`}><Icon name={icon}/><span>{label}</span>{label==="Alerts"&&<em>Live</em>}</NavLink>)}<label>Administration</label>{admin.map(([to,label,icon])=><NavLink key={to} to={to} className={({isActive})=>`shell-link ${isActive?"active":""}`}><Icon name={icon}/><span>{label}</span></NavLink>)}</nav>
   <div className="engine-card"><span className="engine-dot"/><div><b>Detection engine</b><small>AASIST · balanced-v1</small></div></div>
   <button className="shell-signout" onClick={()=>void logout()}>Sign out</button>
  </aside>
  {open&&<button className="sidebar-backdrop" aria-label="Close navigation" onClick={()=>setOpen(false)}/>} 
  <section className="app-main">
   <header className="app-topbar"><button className="mobile-menu" onClick={()=>setOpen(true)}><Icon name="menu"/></button><div className="crumbs"><span>Security Console</span><strong>/</strong><b>{title}</b></div><div className="top-actions"><div className="global-search"><Icon name="search"/><input id="global-search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search security events..."/><kbd>⌘ K</kbd></div><button className="top-icon" aria-label="Notifications"><Icon name="bell"/><i/></button><div className="top-profile"><span>{initials}</span><div><b>{name}</b><small>Signed in</small></div></div></div></header>
   <div className="page-stage"><Outlet/></div>
  </section>
 </div>
}