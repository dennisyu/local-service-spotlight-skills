# RSA Mutation Patterns for Google Ads Scripts

## The Challenge

Google Ads Scripts don't provide a direct method to edit individual RSA headline
or description assets in-place through the standard object model. You can't just
call `ad.setHeadline(3, "New Text")`. RSA modifications require either the mutate
API or a create-and-replace approach.

## Approach 1: AdsApp.mutate() (Preferred)

The mutate API can update RSA assets directly using the ad's resource name. This
is the cleanest approach and preserves the ad's performance history.

```javascript
function updateRsaHeadlines(adGroupAd, newHeadlines, newDescriptions) {
  // Get the ad resource name
  // Format: customers/{customer_id}/ads/{ad_id}
  var adId = adGroupAd.ad().getId();
  var customerId = AdsApp.currentAccount().getCustomerId().replace(/-/g, '');
  var resourceName = 'customers/' + customerId + '/ads/' + adId;

  // Build the headlines array
  var headlineAssets = newHeadlines.map(function(h) {
    var asset = {text: h.text};
    if (h.pinnedField) {
      asset.pinnedField = h.pinnedField; // HEADLINE_1, HEADLINE_2, HEADLINE_3
    }
    return asset;
  });

  // Build the descriptions array
  var descriptionAssets = newDescriptions.map(function(d) {
    var asset = {text: d.text};
    if (d.pinnedField) {
      asset.pinnedField = d.pinnedField; // DESCRIPTION_1, DESCRIPTION_2
    }
    return asset;
  });

  var operation = {
    adOperation: {
      update: {
        resourceName: resourceName,
        responsiveSearchAd: {
          headlines: headlineAssets,
          descriptions: descriptionAssets
        }
      },
      updateMask: 'responsive_search_ad.headlines,responsive_search_ad.descriptions'
    }
  };

  if (CONFIG.DRY_RUN) {
    Logger.log('[DRY RUN] Would update ad ' + adId + ':');
    Logger.log('  New headlines: ' + newHeadlines.map(function(h) { return h.text; }).join(' | '));
    Logger.log('  New descriptions: ' + newDescriptions.map(function(d) { return d.text; }).join(' | '));
    return {success: true, dryRun: true};
  }

  var result = AdsApp.mutate(operation);
  if (result.isSuccessful()) {
    Logger.log('Successfully updated ad ' + adId);
    return {success: true, dryRun: false};
  } else {
    var error = result.getErrorMessages().join('; ');
    Logger.log('Error updating ad ' + adId + ': ' + error);
    return {success: false, error: error};
  }
}
```

### Important Notes on mutate():

- The `updateMask` field tells the API which fields to update. Only include the
  fields you're changing.
- When updating headlines or descriptions, you must provide the COMPLETE list,
  not just the ones you're changing. The API replaces the entire array.
- Pin positions use the enum: `HEADLINE_1`, `HEADLINE_2`, `HEADLINE_3`,
  `DESCRIPTION_1`, `DESCRIPTION_2`.
- The customer ID must have dashes stripped (1234567890, not 123-456-7890).

## Approach 2: Create and Replace (Fallback)

If the mutate approach fails (some account configurations have issues), the
fallback is to create a new ad with the desired assets and pause the old one.

```javascript
function replaceRsa(adGroup, oldAd, newHeadlines, newDescriptions) {
  if (CONFIG.DRY_RUN) {
    Logger.log('[DRY RUN] Would create new RSA and pause old ad ' + oldAd.getId());
    return;
  }

  // Create the new ad
  var adBuilder = adGroup.newAd().responsiveSearchAdBuilder();

  newHeadlines.forEach(function(h) {
    adBuilder.addHeadline(h.text);
  });

  newDescriptions.forEach(function(d) {
    adBuilder.addDescription(d.text);
  });

  adBuilder.withFinalUrl(oldAd.urls().getFinalUrl());

  var result = adBuilder.build();

  if (result.isSuccessful()) {
    // Pause the old ad
    oldAd.pause();
    Logger.log('Created new RSA and paused old ad ' + oldAd.getId());
  } else {
    Logger.log('Error creating new RSA: ' + result.getErrors().join('; '));
  }
}
```

### Tradeoffs:

- **Pro**: Simpler code, uses the standard object model
- **Con**: Loses the old ad's performance history. The new ad starts from zero
  and triggers a new learning period. Google will evaluate it fresh.
- **Con**: You can't set pins through the adBuilder (as of 2026). If pins are
  needed, use the mutate approach.

## Reading Current RSA Assets

Before modifying an RSA, read its current state so you can log the before/after:

```javascript
function getCurrentRsaAssets(adGroupAd) {
  var ad = adGroupAd.ad();
  var adId = ad.getId();
  var adGroupId = adGroupAd.getAdGroup().getId();
  var campaignId = adGroupAd.getCampaign().getId();

  // Use GAQL to get RSA details including pinned positions
  var query = 'SELECT ' +
    'ad_group_ad.ad.id, ' +
    'ad_group_ad.ad.responsive_search_ad.headlines, ' +
    'ad_group_ad.ad.responsive_search_ad.descriptions, ' +
    'ad_group_ad.ad.responsive_search_ad.path1, ' +
    'ad_group_ad.ad.responsive_search_ad.path2, ' +
    'ad_group_ad.ad.final_urls ' +
    'FROM ad_group_ad ' +
    'WHERE ad_group_ad.ad.id = ' + adId + ' ' +
    'AND ad_group.id = ' + adGroupId + ' ' +
    'AND campaign.id = ' + campaignId;

  var rows = AdsApp.search(query);
  for (var row of rows) {
    var rsa = row.adGroupAd.ad.responsiveSearchAd;
    if (rsa) {
      return {
        headlines: rsa.headlines || [],
        descriptions: rsa.descriptions || [],
        path1: rsa.path1 || '',
        path2: rsa.path2 || '',
        finalUrls: row.adGroupAd.ad.finalUrls || []
      };
    }
  }
  return null;
}
```

## Finding Ads by Campaign/Ad Group Name

Most change scripts identify ads by campaign and ad group name (since that's how
the MAA references them). Here's the lookup pattern:

```javascript
function findAdsInAdGroup(campaignName, adGroupName) {
  var ads = AdsApp.ads()
    .withCondition('campaign.name = "' + campaignName + '"')
    .withCondition('ad_group.name = "' + adGroupName + '"')
    .withCondition('ad_group_ad.status != REMOVED')
    .get();

  var results = [];
  while (ads.hasNext()) {
    results.push(ads.next());
  }
  return results;
}
```
