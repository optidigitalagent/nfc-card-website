-- Add the third public locale while preserving reviews and approved translations.
ALTER TABLE client_reviews
  DROP CONSTRAINT client_reviews_locale_check,
  ADD CONSTRAINT client_reviews_locale_check CHECK(locale IN ('uk','en','pl'));
ALTER TABLE client_review_translations
  DROP CONSTRAINT client_review_translations_locale_check,
  ADD CONSTRAINT client_review_translations_locale_check CHECK(locale IN ('uk','en','pl'));
