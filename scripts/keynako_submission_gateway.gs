const GITHUB_API_VERSION = '2022-11-28';

function doPost(event) {
  try {
    if (!event || !event.postData || event.postData.length > 16384) {
      throw new Error('Invalid request body');
    }
    const submission = JSON.parse(event.postData.contents);
    validateSubmission(submission);

    const properties = PropertiesService.getScriptProperties();
    const token = properties.getProperty('GITHUB_TOKEN');
    const owner = properties.getProperty('GITHUB_OWNER') || 'StupidGame';
    const repository = properties.getProperty('GITHUB_REPOSITORY') ||
      'keynako_hotfix_dictionary_storage';
    if (!token) throw new Error('GITHUB_TOKEN is not configured');

    const response = UrlFetchApp.fetch(
      `https://api.github.com/repos/${owner}/${repository}/dispatches`,
      {
        method: 'post',
        contentType: 'application/json',
        headers: {
          Accept: 'application/vnd.github+json',
          Authorization: `Bearer ${token}`,
          'X-GitHub-Api-Version': GITHUB_API_VERSION,
        },
        payload: JSON.stringify({
          event_type: 'keynako_dictionary_submission',
          client_payload: submission,
        }),
        muteHttpExceptions: true,
      },
    );
    const status = response.getResponseCode();
    if (status < 200 || status >= 300) {
      throw new Error(`GitHub dispatch failed (${status})`);
    }
    return jsonResponse({ok: true});
  } catch (error) {
    console.error(error);
    return jsonResponse({ok: false, error: String(error.message || error)});
  }
}

function validateSubmission(value) {
  if (!value || typeof value !== 'object') throw new Error('Payload must be an object');
  if (typeof value.word !== 'string' || !value.word.trim() || value.word.length > 128) {
    throw new Error('Invalid word');
  }
  if (typeof value.ruby !== 'string' || !value.ruby.trim() || value.ruby.length > 256) {
    throw new Error('Invalid ruby');
  }
  if (!Number.isInteger(value.importance) || value.importance < 1 || value.importance > 5) {
    throw new Error('Invalid importance');
  }
  if (value.categories !== undefined &&
      (!Array.isArray(value.categories) || value.categories.length > 10)) {
    throw new Error('Invalid categories');
  }
}

function jsonResponse(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
