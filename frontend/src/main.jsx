
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

function App() {
  const [q,setQ]=useState("");
  const [photos,setPhotos]=useState([]);
  const [selected,setSelected]=useState([]);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("Nhập từ khóa để tìm ảnh chất lượng cao.");
  const [warnings,setWarnings]=useState({});
  const [minWidth,setMinWidth]=useState(3840);
  const [minHeight,setMinHeight]=useState(2160);
  const [providers,setProviders]=useState(["unsplash","pexels","pixabay"]);
  const [directUrl,setDirectUrl]=useState("");

  const toggleProvider = p => setProviders(old => old.includes(p)?old.filter(x=>x!==p):[...old,p]);

  async function search(e) {
    e?.preventDefault();
    if(q.trim().length<2) return setMessage("Vui lòng nhập ít nhất 2 ký tự.");
    setBusy(true); setPhotos([]); setSelected([]); setWarnings({});
    setMessage("Đang tìm kiếm...");
    try {
      const r=await fetch("/api/search",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({q,page:1,per_page:40,min_width:Number(minWidth),min_height:Number(minHeight),providers})});
      const data=await r.json();
      if(!r.ok) throw new Error(data.detail||"Không thể tìm kiếm");
      setPhotos(data.results||[]); setWarnings(data.warnings||{});
      setMessage(`Tìm thấy ${data.count||0} ảnh đạt điều kiện kích thước.`+(data.translated?` Đã tìm bằng từ khóa tiếng Anh: "${data.searched_query}".`:""));
    } catch(err){setMessage("Lỗi: "+err.message);}
    finally{setBusy(false);}
  }

  function toggle(id) { setSelected(old=>old.includes(id)?old.filter(x=>x!==id):[...old,id]); }

  async function addDirectUrl() {
    if (!directUrl.trim()) return;
    setBusy(true);
    try {
      const r=await fetch("/api/add-url",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({url:directUrl.trim(),title:"Website image"})});
      const data=await r.json();
      if(!r.ok) throw new Error(data.detail||"Không thể thêm ảnh");
      if(data.width<Number(minWidth)||data.height<Number(minHeight))
        throw new Error(`Ảnh chỉ có ${data.width} × ${data.height}px, chưa đạt bộ lọc.`);
      setPhotos(old=>[data,...old]);
      setSelected(old=>[...old,"website:"+data.id]);
      setDirectUrl("");
      setMessage("Đã thêm ảnh từ website.");
    } catch(err){setMessage("Không thêm được URL: "+err.message);}
    finally{setBusy(false);}
  }

  async function download() {
    const chosen=photos.filter(p=>selected.includes(p.provider+":"+p.id));
    if(!chosen.length) return setMessage("Hãy chọn ít nhất một ảnh.");
    // Backend nhận tối đa 20 ảnh mỗi ZIP, nên chia thành nhiều ZIP (mỗi ZIP 15 ảnh).
    const SIZE=15, parts=[];
    for(let i=0;i<chosen.length;i+=SIZE) parts.push(chosen.slice(i,i+SIZE));
    setBusy(true);
    try {
      for(let n=0;n<parts.length;n++){
        setMessage(`Đang tạo ZIP ${n+1}/${parts.length}. Vui lòng chờ...`);
        const r=await fetch("/api/download-zip",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({photos:parts[n]})});
        if(!r.ok) {
          let msg="Tải ZIP thất bại ("+r.status+")";
          try{ const d=await r.json(); if(typeof d.detail==="string") msg=d.detail; else if(Array.isArray(d.detail)) msg="Dữ liệu ảnh không hợp lệ: "+d.detail.map(x=>x.msg).join("; "); }catch(_){}
          throw new Error(msg);
        }
        const fileName=parts.length===1?"steven-images.zip":`steven-images-${n+1}.zip`;
        const blob=await r.blob(), url=URL.createObjectURL(blob), a=document.createElement("a");
        a.href=url; a.download=fileName; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
        await new Promise(res=>setTimeout(res,600));
      }
      setMessage(parts.length===1
        ? "Đã tạo file ZIP. Kiểm tra thư mục Downloads và SOURCE_AND_LICENSES.txt."
        : `Đã tạo ${parts.length} file ZIP (steven-images-1.zip ...). Nếu trình duyệt hỏi, hãy cho phép tải nhiều tệp. Kiểm tra thư mục Downloads.`);
    } catch(err){setMessage("Lỗi tải: "+err.message);}
    finally{setBusy(false);}
  }

  return <main>
    <header><div className="brand">SI</div><div><h1>Steven Image Downloader</h1><p>Search · Select · Download</p></div><span className="tag">V1 · LOCAL</span></header>
    <section className="panel">
      <form onSubmit={search}>
        <label>Từ khóa tìm ảnh</label>
        <div className="searchrow"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Ví dụ: mountain landscape, luxury house, technology..." /><button disabled={busy}> {busy?"Đang xử lý...":"Tìm ảnh"} </button></div>
      </form>
      <div className="filters">
        <div><label>Nguồn ảnh</label><div className="checks">
          {["unsplash","pexels","pixabay"].map(p=><label className="check" key={p}><input type="checkbox" checked={providers.includes(p)} onChange={()=>toggleProvider(p)}/>{p}</label>)}
        </div></div>
        <div><label>Chiều rộng tối thiểu</label><input type="number" min="1" value={minWidth} onChange={e=>setMinWidth(e.target.value)}/></div>
        <div><label>Chiều cao tối thiểu</label><input type="number" min="1" value={minHeight} onChange={e=>setMinHeight(e.target.value)}/></div>
      </div>
      <p className="hint">Mặc định lọc ảnh từ 3840 × 2160 px. Kết quả thực tế phụ thuộc ảnh và API của từng nguồn.</p>
      <div className="direct"><label>Thêm ảnh từ website khác (URL ảnh trực tiếp HTTPS)</label>
        <div className="searchrow"><input value={directUrl} onChange={e=>setDirectUrl(e.target.value)} placeholder="https://example.com/photo.jpg"/>
        <button type="button" className="secondary" onClick={addDirectUrl} disabled={busy||!directUrl.trim()}>Thêm URL ảnh</button></div>
        <p className="hint">Dán URL trực tiếp tới tệp ảnh, không phải URL trang bài viết. Website phải cho phép truy cập và tải ảnh.</p>
      </div>
      <div className="status">{message}</div>
      {Object.entries(warnings).map(([k,v])=><div className="warning" key={k}>{k}: {v}</div>)}
    </section>
    <section className="toolbar"><strong>{photos.length} ảnh · Đã chọn {selected.length}</strong><div><button className="secondary" onClick={()=>setSelected(photos.map(p=>p.provider+":"+p.id))} disabled={!photos.length}>Chọn tất cả</button> <button onClick={download} disabled={busy||!selected.length}>Tải ZIP ({selected.length})</button></div></section>
    <section className="grid">
      {photos.map(p=>{const key=p.provider+":"+p.id;return <article className={selected.includes(key)?"photo selected":"photo"} key={key}>
        <img src={p.preview_url} alt={p.title} loading="lazy"/>
        <div className="photoInfo"><label className="pick"><input type="checkbox" checked={selected.includes(key)} onChange={()=>toggle(key)}/> Chọn ảnh</label>
          <b>{p.width} × {p.height}</b><small>{p.provider.toUpperCase()} · {p.photographer}</small>
          <a href={p.page_url} target="_blank" rel="noreferrer">Xem nguồn ảnh ↗</a>
          <small>{p.attribution}</small>
        </div>
      </article>})}
    </section>
    <footer>Steven Image Downloader V1 · Chỉ tải nội dung bạn có quyền sử dụng. Tôn trọng điều khoản và ghi công tác giả.</footer>
  </main>
}
createRoot(document.getElementById("root")).render(<App/>);
