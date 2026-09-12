# Independent visual / UX / responsive review — initial v13 pass

Reviewer role: separate visual, UX, responsive, accessibility and anti-template critic. No implementation changes and no browser process started. This is a preliminary review, not acceptance.

Reviewed direct native captures in `smoke/`: home 390/1440; standard product 390; direct section 390; About 390/1440; corrected ending 390/1440. Compared baseline catalogue, messenger and quote component captures at 390. Read the v13 execution requirements and issue matrix, gallery render/client source, visual-v13.css, about view/CSS. Applied repository project-director/web-studio, design-critic, UX-critic, responsive-review, accessibility-review and anti-template-critic skills.

## Findings for revision / verification

1. **Potential high, needs reproduction** — `/`, 390 px, first viewport: `smoke/home-390.png` shows a completely white lead media rectangle while the 1440 counterpart renders the asset. This may be capture timing, but the evidence cannot currently close the primary media requirement. Accept only after a fresh mobile first viewport demonstrates the lead image and browser load/decode evidence is clean.
2. **Medium** — `/about`, 390 px: `smoke/about-390.png` breaks the H1 into a single-word «засновник» line. This contradicts v13's deliberate heading-wrap goal. Keep the approved wording and adjust the title measure or wrapping so the main phrase reads cohesively; recheck 320/360/390 and EN.
3. **Medium, interaction risk from source** — gallery 2× zoom on touch: `src/visual-v13.css` keeps `touch-action:pan-y pinch-zoom` while zoomed image width becomes 200%. Horizontal touch panning is not enabled. Exercise both image edges with touch in the zoomed state; enable safe panning while suppressing carousel changes as necessary. Source-only finding requires runtime verification.
4. **Pending known composition adjustment** — final CTA vertical band. Main implementer is already adjusting it; do not count an old smoke position as a current unresolved finding. Final acceptance requires current 390×844 capture and geometry.

## Positive evidence / scope discipline

- Desktop catalogue source media fills its assigned column without distortion or artificial side bands; price, free delivery and primary route remain prominent.
- New product gallery exposes recognizable thumbnails with a non-colour active check and indexed sequence. Controls are immediately discoverable; final interaction evidence is still required.
- The corrected footer is compact, light and legible. Native fixed screenshots show the prior contrast issue resolved and contacts no longer form a large stack.
- About follows NFC CARD's graphite/Onest/technical-label vocabulary. Its asymmetric editorial photo chapters and factual timeline serve the owner's specific story; no unrelated visual trend is being imposed.
- No observed need to redesign the accepted v11 navigation, pricing or transactional flow.

## Acceptance remaining

Review the final after matrix, including all eight widths, UA/EN, quote state, messenger states, complete About chapters, gallery modal states, keyboard/zoom/reduced-motion evidence. Current visual acceptance is withheld until the above evidence replaces preliminary smoke captures.

