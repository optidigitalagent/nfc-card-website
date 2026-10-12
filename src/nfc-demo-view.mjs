const copy = {
 uk: {
  situations:{cafe:'Кав’ярня',salon:'Салон',dental:'Стоматологія'}, businesses:{cafe:'Ваша кав’ярня',salon:'Ваш салон',dental:'Ваша стоматологія'},
  situationLabel:'Приклад для вашого бізнесу', sceneTitle:'Очима вашого клієнта', cardHint:'Торкніться картки', connected:'Посилання зчитано',
  ratingHelp:'Оберіть оцінку', ratingSelected:'Ваша оцінка: {n}/5', finishHint:'Лише демо · нічого не надсилаємо', reading:'Зчитування…', openAction:'Відкрити сповіщення', reviewAction:'Обрати оцінку', readyLabel:'Готово до дотику',
  title:'Спробуйте картку прямо тут', intro:'Одне торкання. Знайомий екран. Ваш клієнт сам обирає оцінку та пише відгук.',
  steps:['Прикладіть телефон','Відкрийте сповіщення','Оберіть оцінку'],
  tap:'Прикласти телефон', replay:'Спробувати ще раз', note:'Інтерактивна демонстрація. Реальний відгук не публікується.',
  idle:'Натисніть кнопку, щоб побачити, як працює NFC.', approaching:'Телефон зчитує посилання з картки…',
  notified:'Посилання зчитано. Відкрийте сповіщення на телефоні.', review:'Оберіть будь-яку оцінку та спробуйте написати відгук.',
  done:'Демо завершено. Нічого не опубліковано.', notification:'Відкрити форму відгуку', notificationHint:'NFC · торкніться, щоб відкрити',
  business:'Ваш бізнес', sample:'Приклад форми відгуку', rating:'Ваша оцінка', star:'Оцінка: {n} з 5',
  comment:'Ваш відгук', placeholder:'Як пройшов ваш візит?', finish:'Завершити демо', success:'Дякуємо за знайомство!',
  successNote:'Так клієнт переходить до відгуку. У цій демонстрації дані не надсилаються.',
  order:'Замовити картку', footnote:'Потрібен сумісний смартфон із NFC. Google може попросити увійти в акаунт.',
  screen:'Віртуальний телефон', ready:'Телефон готовий до дотику', badge:'ДЕМО',
 },
 en: {
  situations:{cafe:'Café',salon:'Salon',dental:'Dental clinic'}, businesses:{cafe:'Your café',salon:'Your salon',dental:'Your dental clinic'},
  situationLabel:'An example for your business', sceneTitle:'Through your customer’s eyes', cardHint:'Tap the card', connected:'Link detected',
  ratingHelp:'Choose a rating', ratingSelected:'Your rating: {n}/5', finishHint:'Demo only · no data sent', reading:'Reading…', openAction:'Open notification', reviewAction:'Choose a rating', readyLabel:'Ready to tap',
  title:'Try the card right here', intro:'One tap. A familiar screen. Your customer chooses their own rating and writes their review.',
  steps:['Tap the phone','Open the notification','Choose a rating'],
  tap:'Tap the phone', replay:'Try again', note:'Interactive demo. No real review is published.',
  idle:'Press the button to see how NFC works.', approaching:'The phone is reading the card’s link…',
  notified:'Link detected. Open the notification on the phone.', review:'Choose any rating and try writing a review.',
  done:'Demo complete. Nothing was published.', notification:'Open review form', notificationHint:'NFC · tap to open',
  business:'Your business', sample:'Example review form', rating:'Your rating', star:'Rating: {n} out of 5',
  comment:'Your review', placeholder:'How was your visit?', finish:'Finish demo', success:'Thanks for trying it!',
  successNote:'This is how a customer reaches the review form. This demo sends no data.',
  order:'Order a card', footnote:'A compatible NFC smartphone is required. Google may ask you to sign in.',
  screen:'Virtual phone', ready:'Phone ready to tap', badge:'DEMO',
 },
 pl: {
  situations:{cafe:'Kawiarnia',salon:'Salon',dental:'Stomatologia'}, businesses:{cafe:'Twoja kawiarnia',salon:'Twój salon',dental:'Twój gabinet'},
  situationLabel:'Przykład dla Twojej firmy', sceneTitle:'Oczami Twojego klienta', cardHint:'Dotknij karty', connected:'Link odczytany',
  ratingHelp:'Wybierz ocenę', ratingSelected:'Twoja ocena: {n}/5', finishHint:'Tylko demo · bez wysyłania danych', reading:'Odczytywanie…', openAction:'Otwórz powiadomienie', reviewAction:'Wybierz ocenę', readyLabel:'Gotowy do zbliżenia',
  title:'Wypróbuj kartę tutaj', intro:'Jedno zbliżenie. Znajomy ekran. Klient sam wybiera ocenę i pisze opinię.',
  steps:['Zbliż telefon','Otwórz powiadomienie','Wybierz ocenę'],
  tap:'Zbliż telefon', replay:'Spróbuj ponownie', note:'Interaktywne demo. Prawdziwa opinia nie zostanie opublikowana.',
  idle:'Naciśnij przycisk, aby zobaczyć, jak działa NFC.', approaching:'Telefon odczytuje link z karty…',
  notified:'Link odczytany. Otwórz powiadomienie na telefonie.', review:'Wybierz dowolną ocenę i spróbuj napisać opinię.',
  done:'Demo zakończone. Nic nie zostało opublikowane.', notification:'Otwórz formularz opinii', notificationHint:'NFC · dotknij, aby otworzyć',
  business:'Twoja firma', sample:'Przykładowy formularz opinii', rating:'Twoja ocena', star:'Ocena: {n} z 5',
  comment:'Twoja opinia', placeholder:'Jak oceniasz swoją wizytę?', finish:'Zakończ demo', success:'Dziękujemy za wypróbowanie!',
  successNote:'Tak klient przechodzi do formularza opinii. To demo nie wysyła żadnych danych.',
  order:'Zamów kartę', footnote:'Wymagany jest zgodny smartfon z NFC. Google może poprosić o zalogowanie.',
  screen:'Wirtualny telefon', ready:'Telefon gotowy do zbliżenia', badge:'DEMO',
 },
};

const symbols={cafe:'☕',salon:'✦',dental:'✚'};
const nfcIcon=`<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M11 10a9 9 0 0 1 0 12m5-16a15 15 0 0 1 0 20m5-24a21 21 0 0 1 0 28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="6" cy="16" r="2" fill="currentColor"/></svg>`;
export function nfcDemoView({locale,esc,asset}) {
 const c=copy[locale]||copy.uk;
 return `<section class="nfc-demo" data-nfc-demo data-state="idle" data-situation="cafe" aria-labelledby="nfc-demo-title">
  <div class="nfc-demo-copy">
   <p class="eyebrow"><span class="nfc-demo-live-dot" aria-hidden="true"></span> NFC · LIVE DEMO</p>
   <h2 id="nfc-demo-title">${esc(c.title)}</h2><p class="nfc-demo-intro">${esc(c.intro)}</p>
   <div class="nfc-demo-situations" role="group" aria-label="${esc(c.situationLabel)}">${Object.entries(c.situations).map(([key,label])=>`<button type="button" data-demo-situation="${key}" data-business="${esc(c.businesses[key])}" data-symbol="${symbols[key]}" aria-pressed="${key==='cafe'}"><span aria-hidden="true">${symbols[key]}</span>${esc(label)}</button>`).join('')}</div>
  </div>
  <ol class="nfc-demo-steps">${c.steps.map((text,i)=>`<li data-demo-step="${i}"${i===0?' aria-current="step"':''}><span class="nfc-demo-step-number" aria-hidden="true">0${i+1}</span><span>${esc(text)}</span></li>`).join('')}</ol>
  <div class="nfc-demo-controls">
   <div class="nfc-demo-actions"><button type="button" class="button" data-demo-tap data-idle="${esc(c.tap)}" data-approaching="${esc(c.reading)}" data-notified="${esc(c.openAction)}" data-review="${esc(c.reviewAction)}" data-done="${esc(c.replay)}">${esc(c.tap)}<span aria-hidden="true">↗</span></button><button type="button" class="nfc-demo-reset" data-demo-reset aria-label="${esc(c.replay)}" title="${esc(c.replay)}" disabled>↻</button></div>
   <p class="nfc-demo-status" role="status" aria-live="polite" aria-atomic="true" data-demo-status data-idle="${esc(c.idle)}" data-approaching="${esc(c.approaching)}" data-notified="${esc(c.notified)}" data-review="${esc(c.review)}" data-done="${esc(c.done)}">${esc(c.idle)}</p>
  </div>
  <p class="nfc-demo-disclaimer">${esc(c.note)}</p>
  <div class="nfc-demo-visual">
   <div class="nfc-demo-scene-heading"><span>${esc(c.sceneTitle)}</span><span class="nfc-demo-badge">${esc(c.badge)}</span></div>
   <div class="nfc-demo-stage">
    <div class="nfc-demo-orbit" aria-hidden="true"></div>
    <button class="nfc-demo-card" type="button" data-demo-card-tap aria-label="${esc(c.cardHint)}"><img src="${asset('01-review-card-design-render.webp').url}" alt="" loading="lazy" width="640" height="640"><span class="nfc-demo-card-cue">${nfcIcon}<span>NFC</span></span></button>
    <div class="nfc-demo-signal" aria-hidden="true"><i></i><i></i><i></i></div>
    <div class="nfc-demo-phone" role="group" aria-label="${esc(c.screen)}">
     <div class="nfc-demo-phone-top" aria-hidden="true"><span>9:41</span><span class="nfc-demo-island"></span><span>▰</span></div>
     <div class="nfc-demo-home" data-demo-home><span class="nfc-demo-lock" aria-hidden="true">⌑</span><span class="nfc-demo-clock" aria-hidden="true">9:41</span><p>${esc(c.readyLabel)}</p><div class="nfc-demo-scan-target" aria-hidden="true">${nfcIcon}</div><button type="button" class="nfc-demo-notification" data-demo-open hidden><span class="nfc-demo-notification-icon" aria-hidden="true">${nfcIcon}</span><span><strong>${esc(c.notification)}</strong><small>${esc(c.notificationHint)}</small></span><span class="nfc-demo-notification-arrow" aria-hidden="true">›</span></button><div class="nfc-demo-home-bottom" aria-hidden="true"><span>◉</span><span>▣</span></div></div>
     <div class="nfc-demo-review" data-demo-review hidden><div class="nfc-demo-review-top"><span class="nfc-demo-badge">${esc(c.badge)}</span><span aria-hidden="true">•••</span></div><span class="nfc-demo-business-symbol" data-demo-symbol aria-hidden="true">${symbols.cafe}</span><h3 data-demo-business>${esc(c.businesses.cafe)}</h3><p>${esc(c.sample)}</p>
      <div class="nfc-demo-stars" role="group" aria-label="${esc(c.rating)}">${[1,2,3,4,5].map(n=>`<button type="button" data-demo-star="${n}" aria-label="${esc(c.star.replace('{n}',n))}" aria-pressed="false">★</button>`).join('')}</div>
      <p class="nfc-demo-rating-note" data-demo-rating-note data-empty="${esc(c.ratingHelp)}" data-selected="${esc(c.ratingSelected)}">${esc(c.ratingHelp)}</p>
      <label for="nfc-demo-comment">${esc(c.comment)}</label><textarea id="nfc-demo-comment" rows="3" maxlength="400" placeholder="${esc(c.placeholder)}" autocomplete="off"></textarea>
      <button type="button" class="nfc-demo-finish" data-demo-finish disabled>${esc(c.finish)}</button>
     </div>
     <div class="nfc-demo-complete" data-demo-complete hidden><span class="nfc-demo-complete-icon" aria-hidden="true">✓</span><h3>${esc(c.success)}</h3><p>${esc(c.successNote)}</p><a href="#request" class="nfc-demo-finish">${esc(c.order)}<span aria-hidden="true">↗</span></a></div>
     <span class="nfc-demo-phone-bottom" aria-hidden="true"></span>
    </div>
    <span class="nfc-demo-scene-label" data-demo-connection data-idle="${esc(c.readyLabel)}" data-connected="${esc(c.connected)}">${nfcIcon}<span>${esc(c.readyLabel)}</span></span>
   </div>
   <p class="nfc-demo-footnote">${esc(c.footnote)}</p>
  </div>
 </section>`;
}
