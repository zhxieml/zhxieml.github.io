(() => {
  "use strict";
  const svgNS = "http://www.w3.org/2000/svg";
  const palette = ["#252525", "#6b8294", "#756e91", "#667e71"];
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const svg = (tag, attrs) => {
    const node = document.createElementNS(svgNS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  };

  document.querySelectorAll("[data-research-interactive]").forEach((root) => {
    const config = JSON.parse(root.querySelector("[data-figure-config]").textContent);
    const host = root.querySelector(".interactive-host");
    const fallback = root.querySelector(".interactive-fallback");
    let panelIndex = 0;
    let hiddenSeries = new Set();
    let currentVector = null;
    let cropCount = 0;

    const sourceCrop = (rect, className, label) => {
      const node = svg("svg", { viewBox: rect.join(" "), class: className, role: "img", "aria-label": label });
      const id=root.id+"-source-crop-"+(cropCount++);
      const defs=svg("defs",{}), clip=svg("clipPath",{id,clipPathUnits:"userSpaceOnUse"});
      clip.append(svg("rect",{x:rect[0],y:rect[1],width:rect[2],height:rect[3]})); defs.append(clip); node.append(defs);
      node.append(svg("image", { href: root.dataset.originalSrc, width: root.dataset.originalWidth, height: root.dataset.originalHeight, "clip-path":"url(#"+id+")" }));
      return node;
    };

    const createTable = (columns, rows, sortable = true) => {
      const wrapper = el("div", "interactive-table-scroll");
      wrapper.tabIndex = 0;
      wrapper.setAttribute("role", "region");
      wrapper.setAttribute("aria-label", "Figure data table");
      const table = el("table");
      const head = el("thead"), tr = el("tr"), body = el("tbody");
      const filters = el("div", "interactive-table-tools");
      const search = el("input");
      search.type = "search";
      search.placeholder = "Filter rows…";
      search.setAttribute("aria-label", "Filter table rows");
      const status = el("span", "interactive-table-status");
      status.setAttribute("role", "status");
      let sortIndex = -1, direction = 1;
      const update = () => {
        let filtered = rows.map((cells, index) => ({ cells, index })).filter(({ cells }) => cells.join(" ").toLowerCase().includes(search.value.toLowerCase()));
        if (sortIndex >= 0) filtered.sort((a, b) => {
          const left = String(a.cells[sortIndex]), right = String(b.cells[sortIndex]);
          const numeric = /^-?\d+(\.\d+)?$/.test(left) && /^-?\d+(\.\d+)?$/.test(right);
          const order = numeric ? Number(left) - Number(right) : left.localeCompare(right);
          return order * direction || a.index - b.index;
        });
        body.replaceChildren();
        filtered.forEach(({ cells }) => {
          const row = el("tr");
          cells.forEach((value, index) => {
            const cell = el(index === 0 ? "th" : "td", "", value);
            if (index === 0) cell.scope = "row";
            row.append(cell);
          });
          body.append(row);
        });
        [...tr.children].forEach((th, index) => {
          if (sortIndex === index) th.setAttribute("aria-sort", direction > 0 ? "ascending" : "descending");
          else th.removeAttribute("aria-sort");
        });
        status.textContent = filtered.length + " / " + rows.length + " rows";
      };
      columns.forEach((column, index) => {
        const th = el("th");
        th.scope = "col";
        if (sortable) {
          const button = el("button", "interactive-sort", column);
          button.type = "button";
          button.addEventListener("click", () => {
            direction = sortIndex === index ? -direction : 1;
            sortIndex = index;
            update();
          });
          th.append(button);
        } else th.textContent = column;
        tr.append(th);
      });
      search.addEventListener("input", update);
      head.append(tr); table.append(head, body); wrapper.append(table);
      filters.append(search, status);
      update();
      return { wrapper, filters };
    };

    const addLegend = (series, onChange) => {
      const legend = el("div", "interactive-series");
      series.forEach(({ name, color }) => {
        const label = el("label");
        const checkbox = el("input");
        checkbox.type = "checkbox";
        checkbox.checked = !hiddenSeries.has(name);
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) hiddenSeries.delete(name); else hiddenSeries.add(name);
          onChange();
        });
        const key = el("span", "series-key");
        key.style.setProperty("--series-color", color);
        key.setAttribute("aria-hidden", "true");
        label.append(checkbox, key, el("span", "", name)); legend.append(label);
      });
      return legend;
    };

    const renderVector = (panel, container) => {
      const axis = el("div", "interactive-axis-title", panel.yTitle);
      const plot = el("div", "interactive-plot");
      const draw = () => {
        const width = Math.max(250, Math.round(container.getBoundingClientRect().width));
        const height = width < 450 ? 255 : 315;
        const left = 35, right = width - 10, top = 10, bottom = height - 26;
        const pw = right - left, ph = bottom - top;
        const node = svg("svg", { viewBox: [0,0,width,height].join(" "), role:"img", "aria-label":panel.label + ": " + panel.yTitle });
        const defs = svg("defs", {}), clip = svg("clipPath", { id:root.id + "-clip" });
        clip.append(svg("rect", { x:left, y:top, width:pw, height:ph })); defs.append(clip); node.append(defs);
        panel.yTicks.forEach((tick) => {
          const y = top + tick.position * ph;
          node.append(svg("line", { x1:left, x2:right, y1:y, y2:y, class:"axis-grid" }));
          const text = svg("text", { x:left-8, y:y+4, "text-anchor":"end", class:"axis-text" });
          text.textContent = tick.label; node.append(text);
        });
        panel.xTicks.forEach((tick) => {
          const text = svg("text", { x:left+tick.position*pw, y:height-5, "text-anchor":"middle", class:"axis-text" });
          text.textContent = tick.label; node.append(text);
        });
        const clipped = svg("g", { "clip-path":"url(#" + root.id + "-clip)" });
        panel.series.forEach((series) => {
          const group = svg("g", { transform:"translate("+left+","+top+") scale("+pw+","+ph+")", "data-series-name":series.name });
          if (hiddenSeries.has(series.name)) group.setAttribute("hidden", "");
          const title = svg("title", {}); title.textContent = series.name; group.append(title);
          series.paths.forEach((path) => group.append(svg("path", {
            d:path.d, fill:"none", stroke:series.color, "stroke-width":1.65,
            "stroke-dasharray":path.dashed ? "4 3" : "none", "vector-effect":"non-scaling-stroke", "stroke-linejoin":"round"
          })));
          clipped.append(group);
        });
        node.append(clipped); plot.replaceChildren(node);
      };
      container.append(axis, plot, el("div", "interactive-axis-title interactive-x-title", panel.xTitle));
      container.append(addLegend(panel.series, draw));
      if (config.baselineLabel) container.append(el("p", "interactive-note", "— —  " + config.baselineLabel));
      currentVector = draw;
      draw();
    };

    const renderBars = (panel, container) => {
      const rows = panel.rows;
      const min = panel.domain ? panel.domain[0] : Math.min(0, ...rows.map((r) => r.value));
      const max = panel.domain ? panel.domain[1] : Math.max(0, ...rows.map((r) => r.value)) * 1.06 || 1;
      const position = (value) => (value - min) / (max - min) * 100;
      const names = [...new Set(rows.map((r) => r.series).filter(Boolean))];
      const colors = new Map(names.map((name, index) => [name, palette[index % palette.length]]));
      const bars = el("div", "interactive-bars");
      const update = () => {
        bars.replaceChildren();
        rows.filter((r) => !r.series || !hiddenSeries.has(r.series)).forEach((r) => {
          const row = el("div", "interactive-bar");
          row.setAttribute("data-published-value", r.value);
          row.title = r.label + ": " + r.display;
          const track = el("div", "interactive-bar-track");
          track.setAttribute("aria-hidden", "true");
          if (min < 0) { const zero=el("span", "interactive-zero"); zero.style.left=position(0)+"%"; track.append(zero); }
          const fill = el("span", "interactive-bar-fill");
          fill.style.left = position(Math.min(0,r.value)) + "%";
          fill.style.width = Math.abs(r.value) / (max-min) * 100 + "%";
          fill.style.setProperty("--series-color", colors.get(r.series) || palette[0]);
          track.append(fill);
          row.append(el("span", "interactive-bar-label", r.label), track, el("span", "interactive-bar-value", r.display));
          bars.append(row);
        });
        const axis=el("div", "interactive-bar-axis");
        [...new Set([min, ...(min<0 ? [0] : []), max])].forEach((value) => {
          const tick=el("span", "", Number(value.toPrecision(3)).toString()); tick.style.left=position(value)+"%"; axis.append(tick);
        });
        bars.append(axis);
      };
      container.append(el("div", "interactive-axis-title", panel.axis));
      if (panel.category) container.append(el("div", "interactive-category-title", panel.category));
      container.append(bars);
      if (names.length) container.append(addLegend(names.map((name) => ({ name, color:colors.get(name) })), update));
      if (panel.reference) {
        const references=el("div", "interactive-reference");
        panel.reference.forEach((r) => { const item=el("span", "", r.label+" "); item.append(el("strong", "", r.display)); references.append(item); });
        container.append(references);
      }
      if (panel.note) container.append(el("p", "interactive-note", panel.note));
      const data=el("details", "interactive-data"); data.append(el("summary", "", "Data"));
      const table=createTable([panel.category || "Item",panel.axis], rows.map((r) => [r.label,r.display]));
      data.append(table.filters,table.wrapper); container.append(data);
      update();
    };

    const render = () => {
      const panel=config.panels[panelIndex];
      currentVector=null;
      host.replaceChildren();
      const toolbar=el("div", "interactive-toolbar");
      const control=el("div", "interactive-panel-control");
      if (config.panels.length>1) {
        const label=el("label", "", config.panels.every((p) => /^\d-Step CoTs$/.test(p.label)) ? "CoT length" : "View");
        label.htmlFor=root.id+"-view";
        if (config.panels.every((p) => /^\d-Step CoTs$/.test(p.label))) {
          const input=el("input"); input.type="range"; input.id=label.htmlFor;
          input.min="0"; input.max=config.panels.length-1; input.step="1"; input.value=panelIndex;
          input.setAttribute("aria-valuetext", panel.label);
          const output=el("output", "", panel.label); output.htmlFor=input.id;
          // Keep the focused slider alive while replacing only its result panel.
          input.addEventListener("input", () => {
            panelIndex=Number(input.value);
            const replacement=config.panels[panelIndex]; output.textContent=replacement.label;
            input.setAttribute("aria-valuetext", replacement.label);
            drawPanel(replacement);
          });
          control.append(label,input,output);
        } else {
          const select=el("select"); select.id=label.htmlFor;
          config.panels.forEach((p,index) => { const option=el("option","",p.label); option.value=index; option.selected=index===panelIndex; select.append(option); });
          select.addEventListener("change", () => { panelIndex=Number(select.value); drawPanel(config.panels[panelIndex]); });
          control.append(label,select);
        }
      } else control.append(el("span", "interactive-plot-title", panel.label));
      const reset=el("button", "interactive-reset", "Reset"); reset.type="button";
      reset.addEventListener("click", () => { panelIndex=0; hiddenSeries.clear(); render(); host.querySelector("select,input,button")?.focus({preventScroll:true}); });
      toolbar.append(control,reset); host.append(toolbar);
      const result=el("div", "interactive-result"); host.append(result);
      function drawPanel(selected) {
        result.replaceChildren(); currentVector=null;
        if (selected.kind==="vector") renderVector(selected,result);
        else if (selected.kind==="bars") renderBars(selected,result);
        else if (selected.kind==="table") {
          const table=createTable(selected.columns,selected.rows); result.append(table.filters,table.wrapper);
        } else if (selected.kind==="source-panel") {
          const graphic=sourceCrop(selected.rect,"source-panel-view",selected.label);
          result.append(graphic);
          if (selected.legendItems) {
            if (selected.legendHeading) result.append(el("div","interactive-source-legend-heading",selected.legendHeading));
            const legend=el("div","interactive-source-legend");
            selected.legendItems.forEach((item)=>{
              const label=el("span"), key=el("span","series-key"); key.style.setProperty("--series-color",item.color); key.setAttribute("aria-hidden","true");
              label.append(key,el("span","",item.name)); legend.append(label);
            });
            result.append(legend);
          } else if (selected.legend) result.append(sourceCrop(selected.legend,"source-panel-legend","Legend"));
        } else if (selected.kind==="transcript") {
          const transcript=el("div","interactive-transcript");
          selected.turns.forEach(([role,text]) => {
            const turn=el("div","interactive-turn"), body=el("div","interactive-turn-text");
            const marks=(selected.underlines || []).map((part)=>({start:text.indexOf(part),text:part})).filter((mark)=>mark.start>=0).sort((a,b)=>a.start-b.start);
            let cursor=0;
            marks.forEach((mark)=>{ body.append(document.createTextNode(text.slice(cursor,mark.start)),el("u","",mark.text)); cursor=mark.start+mark.text.length; });
            body.append(document.createTextNode(text.slice(cursor)));
            turn.append(el("div","interactive-turn-role",role),body); transcript.append(turn);
          });
          result.append(transcript);
        }
      }
      drawPanel(panel);
    };

    host.hidden=false;
    render();
    fallback.hidden=true;
    let resizeFrame;
    window.addEventListener("resize", () => {
      if (!currentVector) return;
      cancelAnimationFrame(resizeFrame);
      resizeFrame=requestAnimationFrame(() => currentVector?.());
    }, {passive:true});
  });

})();
