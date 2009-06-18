<?php

function a() {
  print __FUNCTION__ . "\n";
  c();
  c();
}

function b() {
  print __FUNCTION__ . "\n";
  c();
  c();
}

function c() {
  print " " . __FUNCTION__ . "\n";
  d();
}

function d() {
  print "  " . __FUNCTION__ . "\n";
}

a();
a();
b();
register_shutdown_function('b');

?>