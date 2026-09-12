# Independent visual revision recheck 1

Native revised `smoke/about-heading-fixed-320.png` and `about-heading-fixed-390.png` inspected: the approved H1 now occupies three coherent lines without the prior single-word line. Initial finding 2 closed visually at these widths; final EN/matrix evidence remains required.

`smoke/catalog-investigation-390.png` inspected: the lead image renders sharply at full column width, showing essential card/phone content without the old neutral bands. Finding 1's visible symptom closed after the implementer traced the old capture to asynchronous image decode; the final capture utility must await decoding.

`smoke/ending-final-home-390.png` inspected: primary CTA is near the required vertical band, compact footer immediately follows, and labels remain readable. The final heading-size adjustment and final gallery touch interaction evidence remain to be reviewed.

The current stylesheet includes `.image-lightbox[data-zoomed=true] .lightbox-scroll{touch-action:pan-x pan-y pinch-zoom}`. This addresses the source risk; actual touch panning remains pending browser evidence.

No new visual high/critical issue was found in these revised native screenshots. This is a bounded revision recheck, not full candidate acceptance.

