/**
 * RXIQ API — JavaScript/Node.js Usage Examples
 * Install: npm install axios
 */

const axios = require('axios');

// ──────────────────────────────────────────────
// Configuration
// ──────────────────────────────────────────────

const BASE_URL = 'https://rxiq-api.p.rapidapi.com';
const HEADERS = {
  'Content-Type': 'application/json',
  'X-RapidAPI-Key': 'ef7129c761msh9476e78fc3f01ecp1b52dbjsn5620584fb605',
  'X-RapidAPI-Host': 'rxiq-api.p.rapidapi.com',
};

// ──────────────────────────────────────────────
// 1. Extract Content
// ──────────────────────────────────────────────

async function extractContent(url) {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/extract`,
      {
        url: url,
        include_images: true,
        include_links: false,
      },
      { headers: HEADERS }
    );

    const { data } = response.data;
    console.log('Title:', data.title);
    console.log('Word Count:', data.word_count);
    console.log('Excerpt:', data.excerpt);
    return data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// ──────────────────────────────────────────────
// 2. Summarize Content
// ──────────────────────────────────────────────

async function summarizeUrl(url, format = 'bullets') {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/summarize`,
      {
        url: url,
        format: format, // tldr, bullets, key_takeaways, paragraph
        max_length: 200,
        language: 'en',
      },
      { headers: HEADERS }
    );

    const { data } = response.data;
    console.log(`Summary (${data.format}):`);
    console.log(data.summary);
    return data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

async function summarizeText(text, format = 'tldr') {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/summarize`,
      { text, format, max_length: 100 },
      { headers: HEADERS }
    );
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// ──────────────────────────────────────────────
// 3. Sentiment Analysis
// ──────────────────────────────────────────────

async function analyzeSentiment(text) {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/sentiment`,
      { text: text },
      { headers: HEADERS }
    );

    const { data } = response.data;
    console.log(`Sentiment: ${data.sentiment} (${data.confidence.toFixed(2)})`);
    console.log('Key Phrases:', data.key_phrases.join(', '));
    return data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// ──────────────────────────────────────────────
// 4. SEO Metadata
// ──────────────────────────────────────────────

async function extractSEO(url) {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/seo`,
      { url: url },
      { headers: HEADERS }
    );

    const { data } = response.data;
    console.log('Title:', data.title);
    console.log('Meta Description:', data.meta_description);
    console.log('OG Image:', data.open_graph.og_image);
    console.log('Schema Types:', data.schema_markup.types);
    return data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// ──────────────────────────────────────────────
// 5. Full Analysis
// ──────────────────────────────────────────────

async function fullAnalysis(url, summaryFormat = 'bullets') {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/analyze`,
      {
        url: url,
        summary_format: summaryFormat,
        summary_max_length: 200,
      },
      { headers: HEADERS }
    );

    const { data } = response.data;
    console.log('=== CONTENT ===');
    console.log('Title:', data.content.title);
    console.log('Words:', data.content.word_count);
    console.log('\n=== SUMMARY ===');
    console.log(data.summary.summary);
    console.log('\n=== SENTIMENT ===');
    console.log(`${data.sentiment.sentiment} (${data.sentiment.confidence.toFixed(2)})`);
    console.log('\n=== SEO ===');
    console.log('Schema:', data.seo.schema_markup.types);
    console.log(`\nTotal: ${data.total_processing_time_ms}ms`);
    return data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// ──────────────────────────────────────────────
// Run Examples
// ──────────────────────────────────────────────

(async () => {
  const testUrl = 'https://example.com';

  console.log('1. EXTRACT CONTENT');
  await extractContent(testUrl);

  console.log('\n2. SUMMARIZE');
  await summarizeUrl(testUrl);

  console.log('\n3. SENTIMENT');
  await analyzeSentiment('This product is fantastic! Best purchase ever.');

  console.log('\n4. SEO');
  await extractSEO(testUrl);

  console.log('\n5. FULL ANALYSIS');
  await fullAnalysis(testUrl);
})();
