Feature: Make building system build customer's apk into odex format
	 to save boot time.

Scenario: New config does not have corresponding src files
	  Given a new config a20-moxiaoming
	  And no vanzo/cross-platform-packages.mk under source
	  And no vanzo/custom_app under source
	  And no vanzo/custom_app/Android.mk under source
	  When inject apk is called
	  Then injected apk is the only apk in vanzo/cross-platform-packages.mk
	  And injected apk under vendor/custom_app folder
	  And injected apk's info in vencor/custom_app/Android.mk

Scenario: New config have corresponding src files
	  Given a new config a20-moxiaoming
	  And there is vanzo/cross-platform-packages.mk under source
	  And no vanzo/custom_app under source
	  And no vanzo/custom_app/Android.mk under source
	  When inject apk is called
	  Then injected apk is the only apk in vanzo/cross-platform-packages.mk
	  And injected apk under vendor/custom_app folder
	  And injected apk's info in vencor/custom_app/Android.mk

Scenario: Existing config have corresponding overrides
	  Given an existing config a20-moxiaoming
	  And there is vanzo/cross-platform-packages.mk override
	  And there is vanzo/custom_app override
	  And there is vanzo/custom_app/Android.mk override
	  When inject apk is called
	  Then injected apk has been added to vanzo/cross-platform-packages.mk
	  And injected apk has been added to vendor/custom_app folder
	  And injected apk's info has been added to vencor/custom_app/Android.mk