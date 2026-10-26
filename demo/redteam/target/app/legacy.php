<?php
$out = shell_exec($_GET['cmd']);
$obj = unserialize($_POST['data']);
$r = $db->query("SELECT * FROM users WHERE id=".$_GET['id']);
echo $_GET['name'];
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);
