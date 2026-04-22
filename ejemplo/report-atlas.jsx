// Opción B — ATLAS
// Atlas cartográfico de viñedos. Composiciones asimétricas, márgenes anchos,
// numeración a la izquierda. Paleta oliva/ocre/burdeos sobre pergamino.
// Fraunces (alt: EB Garamond) + Inter + JetBrains Mono.

const A = {
  paper: '#ece3d0',
  paperDeep: '#e0d4bb',
  paperDark: '#2a2a22',
  ink: '#1f1e16',
  inkSoft: '#5a5344',
  olive: '#4a5a2a',
  ocher: '#a8772a',
  wine: '#6a1f1f',
  rule: 'rgba(31,30,22,0.25)',
};

function AtlasPage({ n, total, children, style, variant }) {
  const dark = variant === 'dark';
  return (
    <div className="page page-atlas" style={{
      width: 794, minHeight: 1123,
      background: dark ? A.paperDark : A.paper,
      color: dark ? A.paper : A.ink,
      fontFamily: "'EB Garamond', Georgia, serif",
      position: 'relative',
      boxSizing: 'border-box',
      ...style,
    }}>
      {/* side rail w/ folio */}
      <div style={{
        position: 'absolute', top: 0, bottom: 0, left: 0, width: 42,
        borderRight: `0.5px solid ${dark ? 'rgba(236,227,208,0.25)' : A.rule}`,
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        padding: '28px 0 60px',
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
          <img src="assets/geoarga-logo.png" alt="GeoArga" style={{ width: 26, height: 26, objectFit: 'contain', display: 'block' }}/>
          <div style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 4, textTransform: 'uppercase', whiteSpace: 'nowrap', color: dark ? 'rgba(236,227,208,0.6)' : A.inkSoft, marginTop: 80 }}>
            GeoArga · Atlas de viñedos
          </div>
        </div>
        <div style={{ textAlign: 'center', fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', fontSize: 16, color: dark ? A.paper : A.ink }}>
          <div style={{ fontSize: 28 }}>{String(n).padStart(2,'0')}</div>
          <div style={{ width: 16, height: 0.5, background: dark ? A.paper : A.ink, margin: '4px auto' }}/>
          <div style={{ fontSize: 11, color: dark ? 'rgba(236,227,208,0.6)' : A.inkSoft }}>{String(total).padStart(2,'0')}</div>
        </div>
      </div>

      <div style={{ paddingLeft: 72, paddingRight: 52, paddingTop: 56, paddingBottom: 72 }}>
        {children}
      </div>
    </div>
  );
}

function AtlasCover() {
  return (
    <AtlasPage n={1} total={11} variant="dark" style={{ padding: 0 }}>
      <div style={{ position: 'absolute', inset: 0, paddingLeft: 72, paddingRight: 52, paddingTop: 56, paddingBottom: 56 }}>
        {/* Grid of contour-line illustration */}
        <svg viewBox="0 0 680 1000" width="100%" height="100%" style={{ position: 'absolute', inset: 0, opacity: 0.55 }} preserveAspectRatio="xMidYMid slice">
          {Array.from({ length: 14 }).map((_, i) => {
            const y = 120 + i * 55;
            const amp = 20 + i * 2;
            const dPath = `M -20,${y} ` + Array.from({ length: 20 }).map((_, k) => {
              const x = k * 40 - 10;
              const yy = y + Math.sin((k + i) * 0.8) * amp;
              return `L ${x},${yy}`;
            }).join(' ');
            return <path key={i} d={dPath} fill="none" stroke={A.ocher} strokeWidth="0.6" opacity={0.5 + i * 0.03}/>;
          })}
          {/* parcel footprints, tinted */}
          <g transform="translate(200,340)" opacity="0.85">
            <path d="M 0,0 L 180,-40 L 260,80 L 230,200 L 100,240 L -10,180 Z" fill={A.olive} stroke={A.paper} strokeWidth="1" opacity="0.55"/>
            <path d="M 300,30 L 440,-10 L 480,130 L 430,220 L 320,210 L 270,120 Z" fill={A.ocher} stroke={A.paper} strokeWidth="1" opacity="0.5"/>
            <path d="M 40,260 L 290,240 L 380,310 L 370,430 L 220,460 L 60,420 Z" fill={A.wine} stroke={A.paper} strokeWidth="1" opacity="0.5"/>
          </g>
        </svg>

        {/* masthead */}
        <div style={{ position: 'relative', zIndex: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 2.5, textTransform: 'uppercase', color: 'rgba(236,227,208,0.75)' }}>
            <img src="assets/geoarga-logo.png" alt="GeoArga" style={{ height: 72, width: 'auto', display: 'block' }}/>
            <span>Volumen 07 · MMXXV · Copernicus Sentinel-2 L2A</span>
          </div>

          <div>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 11, letterSpacing: 5, textTransform: 'uppercase', color: A.ocher, marginBottom: 20 }}>Atlas de viñedos</div>
            <h1 style={{ margin: 0, fontSize: 120, lineHeight: 0.88, fontFamily: "'EB Garamond', Georgia, serif", fontWeight: 400, letterSpacing: -2, color: A.paper }}>
              Bodega<br/>
              <span style={{ fontStyle: 'italic', color: A.ocher }}>Ejemplo</span>
            </h1>
            <div style={{ marginTop: 32, display: 'grid', gridTemplateColumns: 'repeat(3, auto)', gap: 48, fontFamily: 'Inter, system-ui, sans-serif', fontSize: 11, letterSpacing: 1.5, textTransform: 'uppercase', color: 'rgba(236,227,208,0.75)' }}>
              <div>
                <div style={{ fontSize: 9, marginBottom: 4 }}>Denominación</div>
                <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', textTransform: 'none', fontSize: 18, letterSpacing: 0, color: A.paper }}>Ribera del Duero</div>
              </div>
              <div>
                <div style={{ fontSize: 9, marginBottom: 4 }}>Coordenadas</div>
                <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 13, letterSpacing: 0, color: A.paper }}>41°40′ N · 3°41′ O</div>
              </div>
              <div>
                <div style={{ fontSize: 9, marginBottom: 4 }}>Pase</div>
                <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', textTransform: 'none', fontSize: 18, letterSpacing: 0, color: A.paper }}>28 · VII · 2025</div>
              </div>
            </div>
          </div>

          <div style={{ borderTop: `0.5px solid rgba(236,227,208,0.3)`, paddingTop: 16, display: 'flex', justifyContent: 'space-between', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: 'rgba(236,227,208,0.6)' }}>
            <span>Preparado por GeoArga</span>
            <span style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', textTransform: 'none', fontSize: 14, letterSpacing: 0 }}>
              Monitorización continua desde la baja órbita — 786 km de altura, 10 m de resolución.
            </span>
            <span>Vol. 7 / 11</span>
          </div>
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasSectionMark({ num, kicker, title }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24, marginBottom: 28, alignItems: 'start' }}>
      <div style={{ textAlign: 'right', paddingTop: 6 }}>
        <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', fontSize: 48, color: A.ocher, lineHeight: 1 }}>{num}</div>
      </div>
      <div>
        <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: A.inkSoft }}>{kicker}</div>
        <h2 style={{ margin: '2px 0 0', fontSize: 38, fontWeight: 400, letterSpacing: -0.3, color: A.ink }}>{title}</h2>
      </div>
    </div>
  );
}

function AtlasSummary() {
  const d = window.REPORT_DATA;
  return (
    <AtlasPage n={2} total={11}>
      <AtlasSectionMark num="I" kicker="Resumen" title="Panorámica del predio"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          <p style={{ fontSize: 24, lineHeight: 1.45, fontStyle: 'italic', color: A.ink, margin: 0, textWrap: 'pretty' }}>
            {d.summary}
          </p>

          <div style={{ marginTop: 44, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0, borderTop: `1px solid ${A.ink}`, borderBottom: `1px solid ${A.ink}` }}>
            {[
              { k: 'Superficie', v: '7,2', u: 'ha' },
              { k: 'NDVI medio', v: '0,40', u: 'pond.' },
              { k: 'Δ interanual', v: '−13', u: '%' },
              { k: 'Alertas', v: '1', u: 'activa' },
            ].map((m, i) => (
              <div key={m.k} style={{ padding: '20px 16px', borderRight: i < 3 ? `1px solid ${A.ink}` : 'none' }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft, marginBottom: 4 }}>{m.k}</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 500, fontVariantNumeric: 'tabular-nums', fontSize: 44, color: A.wine, lineHeight: 1, letterSpacing: -1.2 }}>{m.v}</div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, color: A.inkSoft, letterSpacing: 1, textTransform: 'uppercase' }}>{m.u}</div>
                </div>
              </div>
            ))}
          </div>

          {/* client info as marginal colophon */}
          <div style={{ marginTop: 44, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 32 }}>
            <div>
              <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft, marginBottom: 8 }}>Identificación</div>
              <div style={{ fontSize: 16, lineHeight: 1.7, color: A.ink, fontStyle: 'italic' }}>
                {d.client.name}<br/>
                {d.client.do}<br/>
                {d.client.location}
              </div>
            </div>
            <div>
              <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft, marginBottom: 8 }}>Ubicación geográfica</div>
              <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 13, lineHeight: 1.9, color: A.ink }}>
                {d.client.coords}<br/>
                alt. {d.client.altitud}<br/>
                campaña {d.client.campaign}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasLocationContext() {
  const reportData = window.REPORT_DATA;
  const parcelRecords = reportData.parcels || [];
  const totalParcelAreaHa = parcelRecords.reduce((accHa, parcel) => accHa + (parcel.area || 0), 0);
  const weightedAltitudeM = totalParcelAreaHa > 0
    ? parcelRecords.reduce((accAlt, parcel) => accAlt + (parcel.altitude || 0) * (parcel.area || 0), 0) / totalParcelAreaHa
    : 0;
  const weightedSlopePercent = totalParcelAreaHa > 0
    ? parcelRecords.reduce((accSlope, parcel) => accSlope + (parcel.slope || 0) * (parcel.area || 0), 0) / totalParcelAreaHa
    : 0;
  const weightedSlopeDegrees = Math.atan((weightedSlopePercent || 0) / 100) * (180 / Math.PI);
  const dominantOrientationCode = parcelRecords.length
    ? (() => {
        const areaByOrientation = parcelRecords.reduce((accByOrientation, parcel) => {
          const orientationCode = parcel.orientation || 'N/D';
          accByOrientation[orientationCode] = (accByOrientation[orientationCode] || 0) + (parcel.area || 0);
          return accByOrientation;
        }, {});
        return Object.entries(areaByOrientation).sort((a, b) => b[1] - a[1])[0][0];
      })()
    : 'N/D';

  return (
    <AtlasPage n={2} total={11}>
      <AtlasSectionMark num="I" kicker="Contexto geográfico" title="Mapa de localización general"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          <p style={{ fontSize: 17, lineHeight: 1.6, fontStyle: 'italic', color: A.ink, margin: '0 0 20px', maxWidth: 560, textWrap: 'pretty' }}>
            Situación de la finca dentro de su territorio vitícola de referencia. Esta lámina aporta contexto rápido para lectores externos: municipio, comarca y encaje dentro de la denominación de origen.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderTop: `1.5px solid ${A.ink}`, borderBottom: `1.5px solid ${A.ink}`, marginBottom: 20 }}>
            {[
              { k: 'Denominación', v: reportData.client.do },
              { k: 'Municipio', v: reportData.client.location.split(',')[0] || reportData.client.location },
              { k: 'Coordenadas', v: reportData.client.coords },
            ].map((metaItem, index) => (
              <div key={metaItem.k} style={{ padding: '16px 14px', borderRight: index < 2 ? `1px solid ${A.ink}` : 'none' }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>{metaItem.k}</div>
                <div style={{ marginTop: 6, fontSize: 19, lineHeight: 1.25, fontStyle: 'italic', color: A.ink }}>{metaItem.v}</div>
              </div>
            ))}
          </div>

          <div style={{ border: `0.5px solid ${A.ink}`, background: A.paperDeep, padding: 2 }}>
            <div
              style={{
                height: 520,
                background: '#ded2b8',
                backgroundImage: "url('assets/localizacion-general.jpg')",
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }}
            />
          </div>

          <div style={{ marginTop: 20, borderTop: `1px solid ${A.ink}`, borderBottom: `1px solid ${A.ink}`, padding: '16px 0' }}>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.5, textTransform: 'uppercase', color: A.wine, marginBottom: 12, fontWeight: 600 }}>
              Foto topográfica y foto de parcelas (por parcela)
            </div>

            {parcelRecords.map((parcelRecord, parcelIndex) => {
              const parcelSlopeDegrees = Math.atan((parcelRecord.slope || 0) / 100) * (180 / Math.PI);
              return (
                <div key={parcelRecord.id || parcelIndex} style={{ padding: '12px 0 14px', borderTop: parcelIndex === 0 ? 'none' : `0.5px solid ${A.rule}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
                    <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', fontSize: 28, color: A.ink }}>
                      {parcelRecord.name}
                    </div>
                    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.8, textTransform: 'uppercase', color: A.inkSoft }}>
                      {parcelRecord.variety}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 12 }}>
                    <div style={{ border: `0.5px solid ${A.ink}`, background: A.paperDeep, padding: 2 }}>
                      <div
                        style={{
                          height: 160,
                          background: '#d9ceb6',
                          backgroundImage: `url('assets/foto-topografica-${parcelRecord.id}.jpg')`,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          display: 'flex',
                          alignItems: 'flex-end',
                        }}
                      >
                        <div style={{ width: '100%', background: 'rgba(31,30,22,0.62)', color: A.paper, padding: '6px 8px', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase' }}>
                          Foto topográfica · {parcelRecord.id}
                        </div>
                      </div>
                    </div>
                    <div style={{ border: `0.5px solid ${A.ink}`, background: A.paperDeep, padding: 2 }}>
                      <div
                        style={{
                          height: 160,
                          background: '#d9ceb6',
                          backgroundImage: `url('assets/foto-parcelas-${parcelRecord.id}.jpg')`,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          display: 'flex',
                          alignItems: 'flex-end',
                        }}
                      >
                        <div style={{ width: '100%', background: 'rgba(31,30,22,0.62)', color: A.paper, padding: '6px 8px', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase' }}>
                          Foto de parcelas · {parcelRecord.id}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', columnGap: 24, rowGap: 8 }}>
                    {[
                      ['Altitud media de la parcela', `${(parcelRecord.altitude || 0).toFixed(0)} m`],
                      ['Pendiente', `${(parcelRecord.slope || 0).toFixed(1)} % · ${parcelSlopeDegrees.toFixed(1)}°`],
                      ['Orientación', parcelRecord.orientation || 'N/D'],
                      ['Polígonos SIGPAC delimitando la parcela', 'Incluidos en la cartografía'],
                      ['Superficie', `${(parcelRecord.area || 0).toFixed(1)} ha`],
                      ['Municipio y polígono catastral', `${reportData.client.location} · pendiente de detalle catastral`],
                    ].map(([fieldLabel, fieldValue]) => (
                      <div key={`${parcelRecord.id}-${fieldLabel}`} style={{ borderBottom: `0.5px solid ${A.rule}`, paddingBottom: 6 }}>
                        <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase', color: A.inkSoft }}>{fieldLabel}</div>
                        <div style={{ marginTop: 3, fontSize: 16, fontStyle: 'italic', color: A.ink }}>{fieldValue}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasOverview({ layer, setLayer, ramp }) {
  const reportData = window.REPORT_DATA;
  const parcelRecords = reportData.parcels || [];
  const indexCalendarRows = [
    { indexId: 'NDVI', dots: ['◑', '●', '●', '●', '●', '◑'] },
    { indexId: 'NDMI', dots: ['◯', '◑', '●', '●', '●', '◑'] },
    { indexId: 'NDRE', dots: ['◯', '◯', '●', '●', '●', '◑'] },
  ];
  const calendarMonths = ['Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep'];

  return (
    <AtlasPage n={3} total={11}>
      <AtlasSectionMark num="II" kicker="Teledetección" title="Calendario e índices por parcela"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          <div style={{ borderTop: `1px solid ${A.ink}`, borderBottom: `1px solid ${A.ink}`, padding: '14px 0', marginBottom: 18 }}>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.4, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 10 }}>
              Calendario
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '110px repeat(6, 1fr)', gap: 8, alignItems: 'center' }}>
              <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.6, textTransform: 'uppercase', color: A.inkSoft }}>
                Índice
              </div>
              {calendarMonths.map((monthLabel) => (
                <div key={monthLabel} style={{ textAlign: 'center', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.6, textTransform: 'uppercase', color: A.inkSoft }}>
                  {monthLabel}
                </div>
              ))}
              {indexCalendarRows.map((calendarRow) => (
                <React.Fragment key={calendarRow.indexId}>
                  <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 12, color: A.ink }}>
                    {calendarRow.indexId}
                  </div>
                  {calendarRow.dots.map((dot, dotIdx) => (
                    <div key={`${calendarRow.indexId}-${dotIdx}`} style={{ textAlign: 'center', fontSize: 18, color: dot === '●' ? A.olive : dot === '◑' ? A.ocher : A.inkSoft }}>
                      {dot}
                    </div>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.4, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 10 }}>
            Fotos satelitales por parcela (NDVI · NDMI · NDRE)
          </div>

          {parcelRecords.map((parcelRecord, parcelIndex) => (
            <div key={parcelRecord.id || parcelIndex} style={{ marginBottom: 14, border: `0.5px solid ${A.rule}`, background: A.paperDeep, padding: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
                <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', fontSize: 24, color: A.ink }}>
                  {parcelRecord.name}
                </div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.6, textTransform: 'uppercase', color: A.inkSoft }}>
                  {parcelRecord.variety}
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                {[
                  { indexId: 'NDVI', imagePath: `assets/sentinel-ndvi-${parcelRecord.id}.jpg` },
                  { indexId: 'NDMI', imagePath: `assets/sentinel-ndmi-${parcelRecord.id}.jpg` },
                  { indexId: 'NDRE', imagePath: `assets/sentinel-ndre-${parcelRecord.id}.jpg` },
                ].map((indexImage) => (
                  <div key={`${parcelRecord.id}-${indexImage.indexId}`} style={{ border: `0.5px solid ${A.ink}`, background: A.paper, padding: 2 }}>
                    <div
                      style={{
                        height: 190,
                        background: '#d9ceb6',
                        backgroundImage: `url('${indexImage.imagePath}')`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        display: 'flex',
                        alignItems: 'flex-end',
                      }}
                    >
                      <div style={{ width: '100%', background: 'rgba(31,30,22,0.62)', color: A.paper, padding: '5px 7px', fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, letterSpacing: 1.2 }}>
                        {indexImage.indexId}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 10, borderTop: `0.5px solid ${A.rule}`, paddingTop: 10 }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.2, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 8 }}>
                  Índices de vegetación de Sentinel API obtenidos
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                  <div style={{ border: `0.5px solid ${A.rule}`, padding: '8px 10px', background: A.paper }}>
                    <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.inkSoft }}>NDVI</div>
                    <div style={{ marginTop: 3, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600, fontSize: 22, color: A.wine }}>
                      {(parcelRecord.ndvi || 0).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ border: `0.5px solid ${A.rule}`, padding: '8px 10px', background: A.paper }}>
                    <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.inkSoft }}>NDMI</div>
                    <div style={{ marginTop: 3, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600, fontSize: 22, color: A.wine }}>
                      {(parcelRecord.humidity || 0).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ border: `0.5px solid ${A.rule}`, padding: '8px 10px', background: A.paper }}>
                    <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.inkSoft }}>NDRE</div>
                    <div style={{ marginTop: 3, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600, fontSize: 22, color: A.wine }}>
                      {(parcelRecord.ndre || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasTable({ ramp }) {
  const reportData = window.REPORT_DATA;
  const parcelRecords = reportData.parcels || [];
  const fallbackParcel = { id: 'parcela', name: 'Parcela', history: [0.25, 0.29, 0.34, 0.39, 0.43, 0.46, 0.49], ndvi: 0.49 };
  const parcelsForTemporalAnalysis = parcelRecords.length ? parcelRecords : [fallbackParcel];
  const campaignMonths = ['Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep'];

  return (
    <AtlasPage n={4} total={11}>
      <AtlasSectionMark num="III" kicker="Análisis temporal" title="Evolución de campaña y comparativa interanual"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          {parcelsForTemporalAnalysis.map((parcelRecord, parcelIndex) => {
            const sourceHistory = parcelRecord.history || fallbackParcel.history;
            const campaignHistory = sourceHistory.length >= 6 ? sourceHistory.slice(-6) : [...sourceHistory, ...Array(6 - sourceHistory.length).fill(sourceHistory[sourceHistory.length - 1] || 0)];
            return (
            <div key={parcelRecord.id || parcelIndex} style={{ borderTop: parcelIndex === 0 ? `1px solid ${A.ink}` : `0.5px solid ${A.rule}`, paddingTop: 14, marginBottom: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
                <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', fontSize: 28, color: A.ink }}>
                  {parcelRecord.name}
                </div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.8, textTransform: 'uppercase', color: A.inkSoft }}>
                  {parcelRecord.variety || 'Parcela'}
                </div>
              </div>

              <div style={{ borderBottom: `0.5px solid ${A.rule}`, paddingBottom: 14, marginBottom: 14 }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.4, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 8 }}>
                  Gráfica de evolución NDVI mes a mes durante la campaña
                </div>
                <NDVITimeline history={campaignHistory} months={campaignMonths} width={620} height={150} color={A.wine} accent={A.ocher}/>
              </div>

              <div style={{ borderBottom: `0.5px solid ${A.rule}`, paddingBottom: 14, marginBottom: 14 }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.4, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 8 }}>
                  Secuencia de miniaturas mensuales de la parcela
                </div>
                <SmallMultiples parcel={{ ...fallbackParcel, ...parcelRecord, history: campaignHistory }} months={campaignMonths} ramp={ramp}/>
              </div>

              <div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.4, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 8 }}>
                  Comparativa interanual mismo mes año anterior vs actual
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div style={{ border: `0.5px solid ${A.ink}`, background: '#1b1612', padding: 2 }}>
                    <ComparisonMap ramp={ramp} variation={0} width={300} height={220}/>
                    <div style={{ padding: '6px 8px', fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.paper, letterSpacing: 1.2 }}>
                      Año anterior
                    </div>
                  </div>
                  <div style={{ border: `0.5px solid ${A.ink}`, background: '#1b1612', padding: 2 }}>
                    <ComparisonMap ramp={ramp} variation={2} width={300} height={220}/>
                    <div style={{ padding: '6px 8px', fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.paper, letterSpacing: 1.2 }}>
                      Año actual
                    </div>
                  </div>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasParcelPage({ parcel, index, ramp }) {
  const stateColor = parcel.stateTone === 'good' ? A.olive : parcel.stateTone === 'warn' ? A.ocher : A.wine;
  return (
    <AtlasPage n={5 + index} total={11}>
      {/* asymmetric header */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: 32, marginBottom: 28 }}>
        <div>
          <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: A.inkSoft }}>
            IV · {String(index).padStart(2,'0')} / 03 · parcela
          </div>
          <h2 style={{ margin: '6px 0 0', fontSize: 80, fontWeight: 400, letterSpacing: -2, color: A.ink, lineHeight: 0.95, fontStyle: 'italic' }}>
            {parcel.name}
          </h2>
          <div style={{ marginTop: 12, fontSize: 18, fontStyle: 'italic', color: A.inkSoft }}>
            {parcel.variety} · plantada en {parcel.planted} · {parcel.area.toFixed(1)} ha
          </div>
        </div>
        <div style={{
          background: stateColor, color: A.paper, padding: '20px 22px', textAlign: 'right',
          display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        }}>
          <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', opacity: 0.85 }}>Dictamen</div>
          <div style={{ fontSize: 44, fontStyle: 'italic', lineHeight: 1 }}>{parcel.state}</div>
          <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.5, textTransform: 'uppercase', opacity: 0.85, marginTop: 8 }}>
            {parcel.trendLabel} · {parcel.trend === 'up' ? '↗' : parcel.trend === 'down' ? '↘' : '→'}
          </div>
        </div>
      </div>

      {/* map + sidebar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 28 }}>
        <div>
          <div style={{ background: '#1b1612', border: `0.5px solid ${A.ink}`, padding: 2 }}>
            <ParcelZoomMap parcel={parcel} ramp={ramp} width={420} height={320}/>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase', color: A.inkSoft }}>
            <span>Plancha IV.{index} · detalle NDVI</span>
            <span>28 · VII · 2025</span>
          </div>

          <div style={{ marginTop: 26 }}>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: A.inkSoft, marginBottom: 8 }}>
              Evolución NDVI · ene – jul 2025
            </div>
            <NDVITimeline history={parcel.history} width={420} height={110} color={A.wine} accent={A.ocher}/>
          </div>
        </div>

        <div>
          {/* key-value rows */}
          <div style={{ borderTop: `1px solid ${A.ink}` }}>
            {[
              ['NDVI', parcel.ndvi.toFixed(2), 'vigor vegetativo'],
              ['NDRE', parcel.ndre.toFixed(2), 'nitrógeno canopia'],
              ['Humedad', parcel.humidity.toFixed(2), 'suelo estimada'],
              ['Altitud', `${parcel.altitude} m`, 'media parcela'],
              ['Pendiente', `${parcel.slope}%`, parcel.orientation],
            ].map(([k, v, desc], i) => (
              <div key={k} style={{ display: 'grid', gridTemplateColumns: '1fr auto', padding: '14px 0', borderBottom: `0.5px solid ${A.rule}`, alignItems: 'baseline' }}>
                <div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>{k}</div>
                  <div style={{ fontSize: 13, fontStyle: 'italic', color: A.inkSoft, marginTop: 2 }}>{desc}</div>
                </div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 500, fontVariantNumeric: 'tabular-nums', fontSize: 32, color: A.wine, letterSpacing: -0.6 }}>{v}</div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 28, background: A.paperDeep, padding: 20 }}>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft, marginBottom: 6 }}>Interpretación</div>
            <p style={{ margin: 0, fontSize: 15, lineHeight: 1.55, fontStyle: 'italic', color: A.ink, textWrap: 'pretty' }}>{parcel.note}</p>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 32 }}>
        <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: A.inkSoft, marginBottom: 10 }}>
          Secuencia · enero a julio 2025
        </div>
        <SmallMultiples parcel={parcel} ramp={ramp}/>
      </div>
    </AtlasPage>
  );
}

function AtlasYield() {
  const reportData = window.REPORT_DATA;
  const parcelRecords = (reportData.parcels || []).slice();
  const nextImageEta = reportData.alerts && reportData.alerts.find((item) => item.level === 'info')
    ? reportData.alerts.find((item) => item.level === 'info').text
    : 'Pendiente de actualización de próxima imagen.';
  const targetNextImageDate = React.useMemo(() => {
    // Para automatización: usar reportData.nextImageAvailableAtISO cuando exista.
    if (reportData.nextImageAvailableAtISO) {
      const parsed = new Date(reportData.nextImageAvailableAtISO);
      if (!Number.isNaN(parsed.getTime())) return parsed;
    }
    const fallback = new Date();
    fallback.setDate(fallback.getDate() + 3);
    fallback.setHours(11, 30, 0, 0);
    return fallback;
  }, [reportData.nextImageAvailableAtISO]);
  const [countdownNow, setCountdownNow] = React.useState(new Date());

  React.useEffect(() => {
    const timerId = setInterval(() => setCountdownNow(new Date()), 1000);
    return () => clearInterval(timerId);
  }, []);

  const countdownMs = Math.max(0, targetNextImageDate.getTime() - countdownNow.getTime());
  const countdownDays = Math.floor(countdownMs / (1000 * 60 * 60 * 24));
  const countdownHours = Math.floor((countdownMs / (1000 * 60 * 60)) % 24);
  const countdownMinutes = Math.floor((countdownMs / (1000 * 60)) % 60);
  const countdownSeconds = Math.floor((countdownMs / 1000) % 60);

  const getStatus = (stateTone) => {
    if (stateTone === 'bad') return 'Alerta';
    if (stateTone === 'warn') return 'Vigilar';
    return 'Óptimo';
  };
  const getTrend = (trend) => {
    if (trend === 'up') return 'Mejora';
    if (trend === 'down') return 'Empeora';
    return 'Estable';
  };
  const getStatusColor = (stateTone) => {
    if (stateTone === 'bad') return A.wine;
    if (stateTone === 'warn') return A.ocher;
    return A.olive;
  };
  const getActions = (stateTone) => {
    if (stateTone === 'bad') {
      return [
        'Revisar riego sectorizado y emisores en la zona crítica antes de 48 h.',
        'Inspección de campo de estrés hídrico y posibles daños localizados.',
        'Programar seguimiento en próximo pase para validar recuperación.',
      ];
    }
    if (stateTone === 'warn') {
      return [
        'Mantener vigilancia de humedad y cobertura vegetal esta semana.',
        'Priorizar visita técnica si no hay precipitación en 7-10 días.',
        'Ajustar riego de apoyo solo si la tendencia empeora.',
      ];
    }
    return [
      'Mantener manejo actual; no se requieren acciones correctivas inmediatas.',
      'Continuar seguimiento ordinario en el próximo pase Sentinel.',
    ];
  };

  parcelRecords.sort((a, b) => {
    const pa = a.stateTone === 'bad' ? 0 : a.stateTone === 'warn' ? 1 : 2;
    const pb = b.stateTone === 'bad' ? 0 : b.stateTone === 'warn' ? 1 : 2;
    return pa - pb;
  });

  return (
    <AtlasPage n={5} total={11}>
      <AtlasSectionMark num="IV" kicker="Recomendaciones" title="Interpretación y recomendaciones"/>
      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          <p style={{ fontSize: 17, lineHeight: 1.6, fontStyle: 'italic', color: A.ink, margin: '0 0 22px', maxWidth: 620, textWrap: 'pretty' }}>
            Síntesis interpretativa orientada a decisión operativa. Se traduce la lectura de índices en lenguaje no técnico, con acciones concretas priorizadas para campo.
          </p>

          {parcelRecords.map((parcelRecord, parcelIndex) => (
            <div key={parcelRecord.id || parcelIndex} style={{ borderTop: parcelIndex === 0 ? `1.5px solid ${A.ink}` : `0.5px solid ${A.rule}`, padding: '16px 0' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 12, alignItems: 'end' }}>
                <div>
                  <div style={{ fontSize: 28, fontStyle: 'italic', color: A.ink, lineHeight: 1 }}>{parcelRecord.name}</div>
                  <div style={{ marginTop: 4, fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.4, textTransform: 'uppercase', color: A.inkSoft }}>
                    {parcelRecord.variety} · {parcelRecord.area.toFixed(1)} ha
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>
                    Dictamen por parcela
                  </div>
                  <div style={{ marginTop: 2, fontSize: 22, fontStyle: 'italic', color: getStatusColor(parcelRecord.stateTone) }}>
                    {getStatus(parcelRecord.stateTone)}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>
                    Tendencia
                  </div>
                  <div style={{ marginTop: 2, fontSize: 22, fontStyle: 'italic', color: A.ink }}>
                    {getTrend(parcelRecord.trend)}
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 10, background: A.paperDeep, border: `0.5px solid ${A.rule}`, padding: '12px 14px' }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.8, textTransform: 'uppercase', color: A.wine, fontWeight: 600 }}>
                  Interpretación (no técnica)
                </div>
                <div style={{ marginTop: 6, fontSize: 15, color: A.ink, fontStyle: 'italic', lineHeight: 1.55, textWrap: 'pretty' }}>
                  {parcelRecord.note}
                </div>
              </div>

              <div style={{ marginTop: 10 }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.8, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 6 }}>
                  Acciones concretas priorizadas
                </div>
                <ol style={{ margin: 0, paddingLeft: 18, fontSize: 14, color: A.ink, lineHeight: 1.5 }}>
                  {getActions(parcelRecord.stateTone).map((actionItem, actionIndex) => (
                    <li key={`${parcelRecord.id}-action-${actionIndex}`} style={{ marginBottom: 4 }}>{actionItem}</li>
                  ))}
                </ol>
              </div>
            </div>
          ))}

          <div style={{ marginTop: 16, borderTop: `1px solid ${A.ink}`, paddingTop: 10 }}>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>
              Fecha próxima imagen disponible
            </div>
            <div style={{ marginTop: 4, fontSize: 17, color: A.ink, fontStyle: 'italic' }}>{nextImageEta}</div>
            <div style={{ marginTop: 8, display: 'inline-flex', gap: 6, alignItems: 'baseline', background: A.paperDeep, border: `0.5px solid ${A.rule}`, padding: '8px 10px' }}>
              <span style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 18, color: A.wine }}>
                {String(countdownDays).padStart(2, '0')}d
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 18, color: A.wine }}>
                {String(countdownHours).padStart(2, '0')}h
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 18, color: A.wine }}>
                {String(countdownMinutes).padStart(2, '0')}m
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 18, color: A.wine }}>
                {String(countdownSeconds).padStart(2, '0')}s
              </span>
            </div>
          </div>
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasCompare({ ramp }) {
  return (
    <AtlasPage n={9} total={11}>
      <AtlasSectionMark num="V" kicker="Comparativa" title="Dos veranos, uno al lado del otro"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          <p style={{ fontSize: 17, lineHeight: 1.6, fontStyle: 'italic', color: A.ink, margin: '0 0 28px', maxWidth: 520, textWrap: 'pretty' }}>
            El mismo predio, fotografiado por el mismo sensor, en dos años distintos. Lo que una visita al campo o un vuelo de dron puntual no permite ver.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {[{ y: '2024', v: 0, label: 'Julio pasado' }, { y: '2025', v: 2, label: 'Julio actual' }].map((s) => (
              <div key={s.y}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
                  <div style={{ fontSize: 50, fontStyle: 'italic', color: A.ocher, lineHeight: 1 }}>{s.y}</div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>{s.label}</div>
                </div>
                <div style={{ background: '#1b1612', border: `0.5px solid ${A.ink}`, padding: 2 }}>
                  <ComparisonMap ramp={ramp} variation={s.v} width={290} height={230}/>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 36, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderTop: `1.5px solid ${A.ink}`, borderBottom: `1.5px solid ${A.ink}` }}>
            {[
              { h: 'Vigor medio', v: '−13%', s: 'respecto al año anterior' },
              { h: 'Zonas en alerta', v: '+1', s: 'Camino Real se suma' },
              { h: 'Humedad edáfica', v: '−41%', s: 'ponderada por superficie' },
            ].map((m, i) => (
              <div key={m.h} style={{ padding: '18px 16px', borderRight: i < 2 ? `1px solid ${A.ink}` : 'none' }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>{m.h}</div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 500, fontVariantNumeric: 'tabular-nums', fontSize: 40, color: A.wine, marginTop: 6, lineHeight: 1, letterSpacing: -1.2 }}>{m.v}</div>
                <div style={{ fontSize: 13, fontStyle: 'italic', color: A.inkSoft, marginTop: 4 }}>{m.s}</div>
              </div>
            ))}
          </div>

          <p style={{ marginTop: 28, fontSize: 15, lineHeight: 1.65, color: A.inkSoft, fontStyle: 'italic', maxWidth: 560, textWrap: 'pretty' }}>
            La primavera 2025 acumuló <b style={{ color: A.wine, fontStyle: 'normal' }}>38% menos de precipitación</b> que la media de la última década. El adelanto del envero y la pérdida de homogeneidad espacial son consistentes con ese déficit.
          </p>
        </div>
      </div>
    </AtlasPage>
  );
}

function AtlasAlerts() {
  const d = window.REPORT_DATA;
  const icon = (lv) => lv === 'alert' ? '⚠' : lv === 'watch' ? '◐' : lv === 'ok' ? '✓' : '◎';
  const color = (lv) => lv === 'alert' ? A.wine : lv === 'watch' ? A.ocher : lv === 'ok' ? A.olive : A.inkSoft;
  return (
    <AtlasPage n={10} total={11}>
      <AtlasSectionMark num="VI" kicker="Acciones" title="Recomendaciones del pase"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          {d.alerts.map((a, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: '56px 1fr 120px', gap: 18,
              padding: '22px 0',
              borderTop: i === 0 ? `1.5px solid ${A.ink}` : `0.5px solid ${A.rule}`,
            }}>
              <div style={{ fontSize: 32, color: color(a.level), fontFamily: 'Inter, system-ui, sans-serif', lineHeight: 1 }}>{icon(a.level)}</div>
              <div>
                <div style={{ fontStyle: 'italic', fontSize: 24, color: A.ink, lineHeight: 1.1 }}>{a.parcel}</div>
                <div style={{ fontSize: 15, color: A.inkSoft, marginTop: 6, textWrap: 'pretty' }}>{a.text}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: color(a.level), fontWeight: 600 }}>
                  {a.level === 'alert' ? 'Prioridad alta' : a.level === 'watch' ? 'Vigilar' : a.level === 'ok' ? 'Sin acción' : 'Información'}
                </div>
              </div>
            </div>
          ))}

        </div>
      </div>

    </AtlasPage>
  );
}

function AtlasMethodology() {
  const sources = [
    {
      num: 'i',
      name: 'SIGPAC',
      full: 'Sistema de Información Geográfica de Parcelas Agrícolas',
      authority: 'FEGA · Ministerio de Agricultura, Pesca y Alimentación',
      role: 'Delimitación oficial del parcelario',
      detail: 'Fuente catastral de referencia para la identificación y medición de recintos agrícolas en España. Las superficies declaradas en este informe se derivan directamente del vuelo SIGPAC más reciente, garantizando trazabilidad administrativa con la PAC.',
      update: 'Actualización anual',
      res: 'Precisión sub-métrica',
    },
    {
      num: 'ii',
      name: 'Sentinel-2',
      full: 'Constelación Sentinel-2 A / B / C',
      authority: 'Programa Copernicus · Agencia Espacial Europea (ESA)',
      role: 'Índices de vegetación (NDVI · NDRE · NDMI)',
      detail: 'Imágenes multiespectrales de 13 bandas. Se emplean las bandas del rojo, infrarrojo cercano y borde rojo para calcular índices de vigor y humedad. Procesamos únicamente observaciones con cobertura nubosa inferior al 10 % sobre la finca.',
      update: 'Pase cada 3–5 días',
      res: '10 m por píxel',
    },
    {
      num: 'iii',
      name: 'MDT LiDAR',
      full: 'Modelo Digital del Terreno · PNOA-LiDAR',
      authority: 'Instituto Geográfico Nacional (IGN)',
      role: 'Altitud, pendiente y orientación',
      detail: 'Elevaciones derivadas del vuelo LiDAR nacional. A partir del MDT calculamos la pendiente en grados y la orientación de cada recinto, variables determinantes en el régimen térmico e hídrico del viñedo.',
      update: 'Cobertura nacional PNOA',
      res: '2 m por píxel',
    },
  ];
  return (
    <AtlasPage n={11} total={11}>
      <AtlasSectionMark num="VII" kicker="Procedencia" title="Metodología y fuentes"/>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
        <div></div>
        <div>
          <p style={{ fontSize: 17, lineHeight: 1.6, fontStyle: 'italic', color: A.ink, margin: '0 0 28px', maxWidth: 560, textWrap: 'pretty' }}>
            Este informe se construye exclusivamente a partir de fuentes públicas oficiales de alta fiabilidad. Ningún dato es interpolado manualmente: todo procede de sistemas con trazabilidad institucional y cobertura nacional certificada.
          </p>

          {sources.map((s, i) => (
            <div key={s.num} style={{
              display: 'grid', gridTemplateColumns: '60px 1fr 140px', gap: 20,
              padding: '22px 0',
              borderTop: i === 0 ? `1.5px solid ${A.ink}` : `0.5px solid ${A.rule}`,
            }}>
              <div style={{ fontFamily: "'EB Garamond', Georgia, serif", fontStyle: 'italic', fontSize: 28, color: A.wine, lineHeight: 1 }}>
                {s.num}.
              </div>
              <div>
                <div style={{ fontStyle: 'italic', fontSize: 26, color: A.ink, lineHeight: 1.05 }}>{s.name}</div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.5, textTransform: 'uppercase', color: A.inkSoft, marginTop: 4 }}>
                  {s.full}
                </div>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1, textTransform: 'uppercase', color: A.olive, marginTop: 2, fontWeight: 600 }}>
                  {s.authority}
                </div>
                <div style={{ fontSize: 13, color: A.inkSoft, marginTop: 10, fontStyle: 'italic' }}>
                  {s.role}
                </div>
                <div style={{ fontSize: 13, color: A.ink, marginTop: 6, lineHeight: 1.55, textWrap: 'pretty' }}>
                  {s.detail}
                </div>
              </div>
              <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 4 }}>
                <div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 8, letterSpacing: 1.5, textTransform: 'uppercase', color: A.inkSoft }}>Cadencia</div>
                  <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 11, color: A.ink, marginTop: 2 }}>{s.update}</div>
                </div>
                <div>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 8, letterSpacing: 1.5, textTransform: 'uppercase', color: A.inkSoft }}>Resolución</div>
                  <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 11, color: A.ink, marginTop: 2 }}>{s.res}</div>
                </div>
              </div>
            </div>
          ))}

          <div style={{ marginTop: 32, padding: '20px 22px', background: A.paperDeep, border: `0.5px solid ${A.ink}` }}>
            <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.wine, fontWeight: 600 }}>
              Proceso
            </div>
            <div style={{ fontSize: 13, color: A.ink, marginTop: 8, lineHeight: 1.6, textWrap: 'pretty' }}>
              Intersectamos el parcelario SIGPAC con cada escena Sentinel-2 disponible del periodo, descartamos píxeles con nubes o sombra, promediamos los índices por recinto y los cruzamos con el MDT para obtener variables fisiográficas. El resultado es un histórico continuo, comparable entre campañas y auditable frente a las fuentes originales.
            </div>
          </div>

          <div style={{ marginTop: 18, fontSize: 11, lineHeight: 1.55, color: A.inkSoft, fontStyle: 'italic', textWrap: 'pretty' }}>
            Datos bajo licencias abiertas compatibles con uso comercial: SIGPAC (Ministerio de Agricultura), Copernicus Sentinel data 2025 (ESA) y PNOA-LiDAR (© Instituto Geográfico Nacional de España).
          </div>
        </div>
      </div>

      <div style={{ marginTop: 24, textAlign: 'right', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 3, textTransform: 'uppercase', color: A.inkSoft }}>
        GeoArga · MMXXVI · fin
      </div>
    </AtlasPage>
  );
}

function AtlasSectionI_Paginated() {
  const d = window.REPORT_DATA;
  const parcels = d.parcels || [];
  return (
    <>
      <AtlasPage n={2} total={11}>
        <AtlasSectionMark num="I" kicker="Contexto geográfico" title="Mapa de localización general"/>
        <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
          <div></div>
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', borderTop: `1.5px solid ${A.ink}`, borderBottom: `1.5px solid ${A.ink}`, marginBottom: 20 }}>
              {[{ k: 'Denominación', v: d.client.do }, { k: 'Municipio', v: d.client.location.split(',')[0] || d.client.location }, { k: 'Coordenadas', v: d.client.coords }].map((m, i) => (
                <div key={m.k} style={{ padding: '16px 14px', borderRight: i < 2 ? `1px solid ${A.ink}` : 'none' }}>
                  <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>{m.k}</div>
                  <div style={{ marginTop: 6, fontSize: 19, lineHeight: 1.25, fontStyle: 'italic', color: A.ink }}>{m.v}</div>
                </div>
              ))}
            </div>
            <div style={{ border: `0.5px solid ${A.ink}`, background: A.paperDeep, padding: 2 }}>
              <div style={{ height: 520, background: '#ded2b8', backgroundImage: "url('assets/localizacion-general.jpg')", backgroundSize: 'cover', backgroundPosition: 'center' }}/>
            </div>
          </div>
        </div>
      </AtlasPage>
      {parcels.map((p, i) => {
        const slopeDeg = Math.atan((p.slope || 0) / 100) * (180 / Math.PI);
        return (
          <AtlasPage key={`i-${p.id || i}`} n={3 + i} total={11}>
            <AtlasSectionMark num="I" kicker="Ficha topográfica" title={p.name}/>
            <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
              <div></div>
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 12 }}>
                  <div style={{ border: `0.5px solid ${A.ink}`, background: A.paperDeep, padding: 2 }}><div style={{ height: 210, background: '#d9ceb6', backgroundImage: `url('assets/foto-topografica-${p.id}.jpg')`, backgroundSize: 'cover', backgroundPosition: 'center' }}/></div>
                  <div style={{ border: `0.5px solid ${A.ink}`, background: A.paperDeep, padding: 2 }}><div style={{ height: 210, background: '#d9ceb6', backgroundImage: `url('assets/foto-parcelas-${p.id}.jpg')`, backgroundSize: 'cover', backgroundPosition: 'center' }}/></div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', columnGap: 24, rowGap: 8 }}>
                  {[
                    ['Altitud media de la parcela', `${(p.altitude || 0).toFixed(0)} m`],
                    ['Pendiente', `${(p.slope || 0).toFixed(1)} % · ${slopeDeg.toFixed(1)}°`],
                    ['Orientación', p.orientation || 'N/D'],
                    ['Polígonos SIGPAC delimitando la parcela', 'Incluidos en la cartografía'],
                    ['Superficie', `${(p.area || 0).toFixed(1)} ha`],
                    ['Municipio y polígono catastral', `${d.client.location} · pendiente de detalle catastral`],
                  ].map(([k, v]) => (
                    <div key={`${p.id}-${k}`} style={{ borderBottom: `0.5px solid ${A.rule}`, paddingBottom: 6 }}>
                      <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 1.5, textTransform: 'uppercase', color: A.inkSoft }}>{k}</div>
                      <div style={{ marginTop: 3, fontSize: 16, fontStyle: 'italic', color: A.ink }}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </AtlasPage>
        );
      })}
    </>
  );
}

function AtlasSectionII_Paginated() {
  const d = window.REPORT_DATA;
  const parcels = d.parcels || [];
  const months = ['Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep'];
  const rows = [
    { id: 'NDVI', dots: ['◑', '●', '●', '●', '●', '◑'] },
    { id: 'NDMI', dots: ['◯', '◑', '●', '●', '●', '◑'] },
    { id: 'NDRE', dots: ['◯', '◯', '●', '●', '●', '◑'] },
  ];
  return (
    <>
      <AtlasPage n={6} total={11}>
        <AtlasSectionMark num="II" kicker="Teledetección" title="Calendario e índices por parcela"/>
        <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
          <div></div>
          <div style={{ borderTop: `1px solid ${A.ink}`, borderBottom: `1px solid ${A.ink}`, padding: '14px 0' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '110px repeat(6, 1fr)', gap: 8, alignItems: 'center' }}>
              <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.6, textTransform: 'uppercase', color: A.inkSoft }}>Índice</div>
              {months.map((m) => <div key={m} style={{ textAlign: 'center', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 10, letterSpacing: 1.6, textTransform: 'uppercase', color: A.inkSoft }}>{m}</div>)}
              {rows.map((r) => (
                <React.Fragment key={r.id}>
                  <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 12, color: A.ink }}>{r.id}</div>
                  {r.dots.map((d, i) => <div key={`${r.id}-${i}`} style={{ textAlign: 'center', fontSize: 18, color: d === '●' ? A.olive : d === '◑' ? A.ocher : A.inkSoft }}>{d}</div>)}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </AtlasPage>
      {parcels.map((p, i) => (
        <AtlasPage key={`ii-${p.id || i}`} n={7 + i} total={11}>
          <AtlasSectionMark num="II" kicker="Teledetección" title={p.name}/>
          <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
            <div></div>
            <div style={{ border: `0.5px solid ${A.rule}`, background: A.paperDeep, padding: 10 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                {[{ id: 'NDVI', pth: `assets/sentinel-ndvi-${p.id}.jpg` }, { id: 'NDMI', pth: `assets/sentinel-ndmi-${p.id}.jpg` }, { id: 'NDRE', pth: `assets/sentinel-ndre-${p.id}.jpg` }].map((im) => (
                  <div key={im.id} style={{ border: `0.5px solid ${A.ink}`, background: A.paper, padding: 2 }}>
                    <div style={{ height: 230, background: '#d9ceb6', backgroundImage: `url('${im.pth}')`, backgroundSize: 'cover', backgroundPosition: 'center' }}/>
                    <div style={{ padding: '5px 7px', fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, letterSpacing: 1.2 }}>{im.id}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 10, borderTop: `0.5px solid ${A.rule}`, paddingTop: 10 }}>
                <div style={{ fontFamily: 'Inter, system-ui, sans-serif', fontSize: 9, letterSpacing: 2.2, textTransform: 'uppercase', color: A.wine, fontWeight: 600, marginBottom: 8 }}>
                  Índices de vegetación de Sentinel API obtenidos
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                  <div style={{ border: `0.5px solid ${A.rule}`, padding: '8px 10px', background: A.paper }}>
                    <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.inkSoft }}>NDVI</div>
                    <div style={{ marginTop: 3, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600, fontSize: 22, color: A.wine }}>{(p.ndvi || 0).toFixed(2)}</div>
                  </div>
                  <div style={{ border: `0.5px solid ${A.rule}`, padding: '8px 10px', background: A.paper }}>
                    <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.inkSoft }}>NDMI</div>
                    <div style={{ marginTop: 3, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600, fontSize: 22, color: A.wine }}>{(p.humidity || 0).toFixed(2)}</div>
                  </div>
                  <div style={{ border: `0.5px solid ${A.rule}`, padding: '8px 10px', background: A.paper }}>
                    <div style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", fontSize: 10, color: A.inkSoft }}>NDRE</div>
                    <div style={{ marginTop: 3, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600, fontSize: 22, color: A.wine }}>{(p.ndre || 0).toFixed(2)}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </AtlasPage>
      ))}
    </>
  );
}

function AtlasSectionIII_Paginated({ ramp }) {
  const d = window.REPORT_DATA;
  const parcels = d.parcels || [];
  const fallback = { id: 'p', name: 'Parcela', history: [0.3, 0.35, 0.4, 0.45, 0.47, 0.5] };
  return (
    <>
      {(parcels.length ? parcels : [fallback]).map((p, i) => {
        const h = (p.history || fallback.history);
        const series = h.length >= 6 ? h.slice(-6) : [...h, ...Array(6 - h.length).fill(h[h.length - 1] || 0)];
        return (
          <AtlasPage key={`iii-${p.id || i}`} n={10 + i} total={11}>
            <AtlasSectionMark num="III" kicker="Análisis temporal" title={p.name}/>
            <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
              <div></div>
              <div>
                <NDVITimeline history={series} months={['Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep']} width={620} height={150} color={A.wine} accent={A.ocher}/>
                <div style={{ marginTop: 12 }}><SmallMultiples parcel={{ ...fallback, ...p, history: series }} months={['Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep']} ramp={ramp}/></div>
                <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div style={{ border: `0.5px solid ${A.ink}`, background: '#1b1612', padding: 2 }}><ComparisonMap ramp={ramp} variation={0} width={300} height={220}/></div>
                  <div style={{ border: `0.5px solid ${A.ink}`, background: '#1b1612', padding: 2 }}><ComparisonMap ramp={ramp} variation={2} width={300} height={220}/></div>
                </div>
              </div>
            </div>
          </AtlasPage>
        );
      })}
    </>
  );
}

function AtlasSectionIV_Paginated() {
  const d = window.REPORT_DATA;
  const parcels = (d.parcels || []).slice();
  const nextImageEta = d.alerts && d.alerts.find((a) => a.level === 'info') ? d.alerts.find((a) => a.level === 'info').text : 'Pendiente de actualización';
  const status = (t) => t === 'bad' ? 'Alerta' : t === 'warn' ? 'Vigilar' : 'Óptimo';
  const trend = (t) => t === 'up' ? 'Mejora' : t === 'down' ? 'Empeora' : 'Estable';
  const color = (t) => t === 'bad' ? A.wine : t === 'warn' ? A.ocher : A.olive;
  return (
    <>
      {parcels.map((p, i) => (
        <AtlasPage key={`iv-${p.id || i}`} n={13 + i} total={11}>
          <AtlasSectionMark num="IV" kicker="Recomendaciones" title={p.name}/>
          <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}>
            <div></div>
            <div style={{ borderTop: `1px solid ${A.ink}`, paddingTop: 10 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 12, alignItems: 'end' }}>
                <div style={{ fontSize: 26, fontStyle: 'italic' }}>{p.name}</div>
                <div><div style={{ fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>Dictamen por parcela</div><div style={{ fontSize: 22, fontStyle: 'italic', color: color(p.stateTone) }}>{status(p.stateTone)}</div></div>
                <div><div style={{ fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', color: A.inkSoft }}>Tendencia</div><div style={{ fontSize: 22, fontStyle: 'italic' }}>{trend(p.trend)}</div></div>
              </div>
              <div style={{ marginTop: 10, background: A.paperDeep, border: `0.5px solid ${A.rule}`, padding: '12px 14px' }}>{p.note}</div>
            </div>
          </div>
        </AtlasPage>
      ))}
      <AtlasPage n={16} total={11}>
        <AtlasSectionMark num="IV" kicker="Recomendaciones" title="Próxima imagen disponible"/>
        <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24 }}><div></div><div style={{ fontSize: 17, fontStyle: 'italic' }}>{nextImageEta}</div></div>
      </AtlasPage>
    </>
  );
}

function AtlasReport({ layer, setLayer, ramp }) {
  const d = window.REPORT_DATA;
  return (
    <>
      <AtlasCover/>
      <AtlasSectionI_Paginated/>
      <AtlasSectionII_Paginated/>
      <AtlasSectionIII_Paginated ramp={ramp}/>
      <AtlasSectionIV_Paginated/>
      {d.parcels.map((p, i) => <AtlasParcelPage key={p.id} parcel={p} index={i + 1} ramp={ramp}/>)}
      <AtlasCompare ramp={ramp}/>
      <AtlasAlerts/>
      <AtlasMethodology/>
    </>
  );
}

Object.assign(window, { AtlasReport });
