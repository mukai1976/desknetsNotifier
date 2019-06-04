# desknetsNotifier
デスクネッツの当日スケジュールをSlackへpush通知する  
（参考にさせて頂いたサイト：https://github.com/kentoku24/desknetsNotifier）

- 使い方
  * conf配下のcredentials.template.yamlを適当なファイル名にリネーム、必要な情報を記入し、このディレクトリ内でpython main.pyを実行  
    パラメータにリネームした(例：./conf/credentials.yaml)を設定 
    - DN_USERNAME DN_PASSWORD DN_URL これらには自分のデスクネッツの情報を記入
    - DN_SELECTOR デスクネッツのスケジュールが表示されているセパレータを記入（メイン）  
      参考（"#jsch-schweekgrp > form > div.sch-gweek.sch-cal-group-week.jsch-cal-list.jco-print-template.sch-data-view-area > div.sch-gcal-target.me.cal-h-cell.jsch-cal > div.cal-h-week > table > tbody > tr > td.cal-day.co-today"）
    - DN_SELECTOR_CL デスクネッツのスケジュールが表示されているセパレータを記入（サブ）  
      参考（" > div:nth-child(2)"）
    - SLACK_TOKEN は[こちら](https://api.slack.com/custom-integrations/legacy-tokens)から取得
    - SLACK_USER_ID は [users.info](https://api.slack.com/methods/users.info/test) あたりで自分のユーザ名リンクをクリック
    - SLACK_CHANNEL 出力するチャンネル名を記入
    - SLACK_MENTION メンションしたい場合記入　フォーマットは"<@メンション先>"

- 前提条件
  * Chrome Canaryを導入したWindows端末で動作確認をしていますので、Windows版のChromeDriverを同梱しています。
  お使いのOSに対応する[ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) をこのディレクトリに置けば動くかもしれません。
